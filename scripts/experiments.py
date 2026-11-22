#!/usr/bin/env python3
"""Reproducible course experiments; Python standard library, Docker, and wrk."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PROJECT = os.environ.get('COMPOSE_PROJECT_NAME', 'cisc7403-project2')
URL = 'http://127.0.0.1:6120'
FILES = {'dual': 'docker-compose.yml', 'single': 'docker-compose.single.yml'}
EXPECTED = {'dual': {'backend1', 'backend2'}, 'single': {'backend1'}}
SOURCE = ['backend/app.py', 'backend/Dockerfile', 'backend/requirements.txt',
          'backend/.dockerignore', *FILES.values(), 'nginx/nginx.conf',
          'nginx/nginx.single.conf', 'scripts/experiments.py',
          'scripts/check_balance.sh', 'scripts/check_failover.sh',
          'scripts/benchmark.sh', 'scripts/set_mode.sh', 'scripts/run_all.sh']


def run(args, output=None, check=True):
    p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text('$ ' + ' '.join(args) + '\n' + p.stdout)
    if check and p.returncode:
        raise RuntimeError(f'Command failed ({p.returncode}): {args}; {p.stdout[-1800:]}')
    return p.stdout


def dc(mode, *args, output=None, check=True):
    return run(['docker', 'compose', '-p', PROJECT, '-f', FILES[mode], *args], output, check)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def hit(phase, path='/'):
    row = {'utc': datetime.now(timezone.utc).isoformat(), 'phase': phase, 'path': path}
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(URL + path, timeout=3) as response:
            row.update(status=response.status, body=json.load(response),
                       content_type=response.headers.get_content_type())
    except urllib.error.HTTPError as error:
        row.update(status=error.code, error=str(error))
    except Exception as error:
        row.update(status=0, error=str(error))
    row['elapsed_ms'] = round((time.perf_counter() - start) * 1000, 3)
    return row


def valid(row):
    return (row['status'] == 200 and row.get('content_type') == 'application/json'
            and row.get('body', {}).get('status') == 'ok')


def samples(out, phase, count, expected, require_all=True):
    rows = []
    for i in range(count):
        rows.append(hit(phase, '/' if i % 2 == 0 else '/work'))
        time.sleep(0.05)
    with (out / 'requests.jsonl').open('a') as f:
        for row in rows:
            f.write(json.dumps(row) + '\n')
    counts = Counter(r.get('body', {}).get('instance', 'ERROR') for r in rows)
    passed = (all(valid(r) for r in rows) and set(counts).issubset(expected)
              and (not require_all or set(counts) == expected))
    summary = {'passed': passed, 'requests': count, 'instances': dict(counts),
               'errors': sum(not valid(r) for r in rows),
               'max_ms': max(r['elapsed_ms'] for r in rows)}
    save(out / (phase + '.json'), summary)
    print(phase, json.dumps(summary), flush=True)
    if not passed:
        raise AssertionError(f'{phase} failed; see {out}')
    return summary


def wait_ready(out, mode):
    rows, seen = [], set()
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        row = hit('readiness')
        rows.append(row)
        if valid(row):
            seen.add(row['body']['instance'])
        if seen == EXPECTED[mode]:
            save(out / 'readiness.json', rows)
            return
        time.sleep(0.2)
    save(out / 'readiness.json', rows)
    raise RuntimeError(f'{mode} did not become ready; instances={seen}')


def switch(mode, out):
    out.mkdir(parents=True, exist_ok=True)
    # The base file knows all three services; remove only this named project.
    dc('dual', 'down', '--remove-orphans', output=out / 'previous-down.log')
    dc(mode, 'up', '--build', '-d', '--remove-orphans', output=out / 'startup.log')
    dc(mode, 'exec', '-T', 'nginx', 'nginx', '-t', output=out / 'nginx-test.txt')
    wait_ready(out, mode)
    inspect(out, mode)


def inspect(out, mode):
    dc(mode, 'config', output=out / 'compose-resolved.yaml')
    conf = dc(mode, 'exec', '-T', 'nginx', 'nginx', '-T', output=out / 'nginx-effective.txt')
    upstream = set(re.findall(r'server (backend[12]):5000;', conf))
    assert upstream == EXPECTED[mode], upstream
    services = set(dc(mode, 'ps', '--services', '--status', 'running').split())
    assert services == EXPECTED[mode] | {'nginx'}, services
    dc(mode, 'ps', '--all', output=out / 'containers.txt')
    ids = dc(mode, 'ps', '-q').split()
    state = json.loads(run(['docker', 'inspect', *ids]))
    images = []
    runtime = []
    for container in state:
        service = container['Config']['Labels']['com.docker.compose.service']
        bindings = container['HostConfig']['PortBindings'] or {}
        item = {'service': service, 'image': container['Image'], 'ports': bindings}
        if service.startswith('backend'):
            assert not bindings, bindings
            images.append(container['Image'])
            processes = run(['docker', 'top', container['Id'], '-eo', 'pid,args'],
                            out / (service + '-processes.txt'))
            assert len(processes.strip().splitlines()) == 2, processes
            info = dc(mode, 'exec', '-T', service, 'python', '-c',
                      'import json; from pathlib import Path; '
                      's=dict(l.split(":",1) for l in Path("/proc/1/status").read_text().splitlines()); '
                      'print(json.dumps({"threads":int(s["Threads"]),'
                      '"cmd":Path("/proc/1/cmdline").read_bytes().decode().replace(chr(0)," ").strip()}))')
            item.update(json.loads(info))
            assert item['threads'] == 1 and item['cmd'] == 'python app.py', item
        else:
            assert set(bindings) == {'80/tcp'}, bindings
            assert all(p['HostPort'] == '6120' for p in bindings['80/tcp']), bindings
        runtime.append(item)
    assert len(set(images)) == 1
    save(out / 'runtime.json', runtime)


def balance(out):
    switch('dual', out)
    return samples(out, 'balance', 40, EXPECTED['dual'])


def failover(out):
    switch('dual', out)
    result = {'initial': samples(out, 'initial', 20, EXPECTED['dual'])}
    try:
        for failed, survivor in [('backend1', 'backend2'), ('backend2', 'backend1')]:
            dc('dual', 'stop', failed, output=out / (failed + '-stop.txt'))
            dc('dual', 'ps', '--all', output=out / (failed + '-stopped-state.txt'))
            result[failed + '-stopped'] = samples(out, failed + '-stopped', 30, {survivor})
            dc('dual', 'start', failed, output=out / (failed + '-start.txt'))
            recovery = out / ('recovery-' + failed)
            recovery.mkdir()
            wait_ready(recovery, 'dual')
            rows = json.loads((recovery / 'readiness.json').read_text())
            assert all(valid(r) for r in rows), rows
            result[failed + '-restored'] = samples(out, failed + '-restored', 20, EXPECTED['dual'])
    finally:
        dc('dual', 'start', 'backend1', 'backend2', output=out / 'restore.txt', check=False)
        dc('dual', 'logs', '--no-color', '--timestamps', output=out / 'container-logs.txt', check=False)
    return result


def latency_ms(value):
    match = re.fullmatch(r'([0-9.]+)(us|ms|s)', value)
    if not match:
        raise ValueError(value)
    return float(match[1]) * {'us': 0.001, 'ms': 1, 's': 1000}[match[2]]


def parse_wrk(raw):
    latency = re.search(r'^\s*Latency\s+(\S+)', raw, re.M)
    throughput = re.search(r'Requests/sec:\s+([0-9.]+)', raw)
    count = re.search(r'(\d+) requests in', raw)
    if not (latency and throughput and count):
        raise RuntimeError('Incomplete wrk output')
    errors = re.search(r'Socket errors: connect (\d+), read (\d+), write (\d+), timeout (\d+)', raw)
    non2xx = re.search(r'Non-2xx or 3xx responses:\s*(\d+)', raw)
    result = {'requests_per_sec': float(throughput[1]), 'avg_latency_ms': latency_ms(latency[1]),
              'requests': int(count[1]), 'socket_errors': sum(map(int, errors.groups())) if errors else 0,
              'non_2xx_3xx': int(non2xx[1]) if non2xx else 0}
    assert result['requests'] > 0 and not result['socket_errors'] and not result['non_2xx_3xx'], result
    return result


def benchmark(out):
    # Alternate modes across three paired trials; exclude warm-ups from summaries.
    all_rows = []
    workload = ['-t2', '-c20', '-d10s', '--timeout', '5s', '--latency', URL + '/work']
    run(['wrk', '--version'], out / 'wrk-version.txt', check=False)
    for trial in range(1, 4):
        for mode in ['single', 'dual']:
            stage = out / f'{trial}-{mode}'
            switch(mode, stage)
            samples(stage, 'preflight', 10, EXPECTED[mode])
            run(['wrk', '-t2', '-c20', '-d3s', '--timeout', '5s', URL + '/work'], stage / 'warmup.txt')
            time.sleep(2)  # Drain outstanding warm-up requests before timed measurement.
            started = datetime.now(timezone.utc).isoformat()
            raw = run(['wrk', *workload], stage / 'wrk.txt')
            row = {'trial': trial, 'mode': mode, 'started_utc': started, **parse_wrk(raw)}
            all_rows.append(row)
            dc(mode, 'logs', '--no-color', '--timestamps', output=stage / 'container-logs.txt')
            print('performance', json.dumps(row), flush=True)
    aggregates = {}
    for mode in ['single', 'dual']:
        selected = [r for r in all_rows if r['mode'] == mode]
        aggregates[mode] = {key: round(sum(r[key] for r in selected) / len(selected), 3)
                            for key in ['requests_per_sec', 'avg_latency_ms']}
    return {'command': ['wrk', *workload], 'warmup_seconds': 3,
            'aggregation': 'Arithmetic mean of three wrk-reported trial values per mode',
            'trials': all_rows, 'mean': aggregates,
            'throughput_ratio': round(aggregates['dual']['requests_per_sec'] /
                                      aggregates['single']['requests_per_sec'], 3)}


def metadata(out):
    out.mkdir(parents=True, exist_ok=True)
    checksums = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCE}
    save(out / 'source-sha256.json', checksums)
    run(['git', 'rev-parse', 'HEAD'], out / 'git-head.txt', check=False)
    run(['git', 'status', '--short'], out / 'git-status.txt', check=False)
    run(['uname', '-srmo'], out / 'vm.txt')
    run(['cat', '/etc/os-release'], out / 'os-release.txt')
    run(['lscpu'], out / 'cpu.txt')
    run(['free', '-h'], out / 'memory.txt')
    run(['docker', 'version'], out / 'docker-version.txt')
    run(['docker', 'compose', 'version'], out / 'compose-version.txt')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=['all', 'balance', 'failover', 'benchmark', 'mode'])
    parser.add_argument('mode', nargs='?', choices=['single', 'dual'])
    args = parser.parse_args()
    if args.task == 'mode' and not args.mode:
        parser.error('mode requires single or dual')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}'
    record = ROOT / 'results' / 'acceptance' / run_id
    metadata(record)
    result = {'run_id': run_id, 'project': PROJECT, 'passed': False, 'experiments': {}}
    try:
        if args.task == 'mode':
            switch(args.mode, record / args.mode)
        else:
            stages = [('balance', 'load_balancing', balance), ('failover', 'fault_tolerance', failover),
                      ('benchmark', 'performance', benchmark)]
            for name, folder, function in stages:
                if args.task not in ('all', name):
                    continue
                out = ROOT / 'results' / folder / run_id
                out.mkdir(parents=True)
                result['experiments'][name] = {'evidence': str(out.relative_to(ROOT))}
                values = function(out)
                save(out / 'summary.json', values)
                dc('dual', 'logs', '--no-color', '--timestamps',
                   output=out / 'container-logs.txt', check=False)
                result['experiments'][name]['passed'] = True
            # Each experiment ends with the normal three-container deployment running.
        result['passed'] = True
    except Exception as error:
        result['error'] = str(error)
        print('FAILED:', error, flush=True)
        dc('dual', 'logs', '--no-color', '--timestamps', output=record / 'failure-logs.txt', check=False)
        # Best effort recovery; preserve the failure instead of hiding it.
        try:
            switch('dual', record / 'failure-recovery')
        except Exception as recovery_error:
            result['recovery_error'] = str(recovery_error)
    finally:
        save(record / 'summary.json', result)
        print('Acceptance record:', record, flush=True)
        print(json.dumps(result, indent=2), flush=True)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

#! /usr/bin/env python3

import sys
import json
import socket
import asyncio
import subprocess

import ipaddress


def main():
    network = parse_args()
    socket.setdefaulttimeout(1)
    machines = {}
    hosts = [str(host) for host in network.hosts()]
    ping_sweep(hosts)
    lines = arp() + arp(['-n'])
    for line in lines:
        parts = line.split()
        if len(parts) < 5:
            continue
        key, _, mac, _, _ = parts

        if not machines.get(mac):
            machines[mac] = {'ip': None, 'hostnames': set()}

        if is_ip(key):
            if key in hosts:
                machines[mac]['ip'] = key
        else:
            machines[mac]['hostnames'].add(key)
    ret = {}
    for mac, v in machines.items():
        v['hostnames'] = list(v['hostnames'])
        for hostname in v['hostnames']:
            if v['ip']:
                ret[hostname] = {'ansible_host': v['ip'], 'macaddress': mac}
        if not v['hostnames'] and v['ip']:
            ret[v['ip']] = {'macaddress': mac}

    print(json.dumps(ret, indent=4, sort_keys=True))


def parse_args():
    args = list(sys.argv)
    if args[0] == 'python':
        args.pop(0)
    if 1 <= len(args) > 2:
        raise Exception("Incorrect arguments")
    return ipaddress.ip_network(args[-1])


def ping_sweep(hosts):
    loop = asyncio.get_event_loop()
    tasks = [ping(host, 22) for host in hosts]
    return loop.run_until_complete(asyncio.wait(tasks))


async def ping(host, port, loop=None):
    fut = asyncio.open_connection(host, port, loop=loop)
    try:
        reader, writer = await asyncio.wait_for(fut, timeout=0.5)
        return host
    except Exception as e:
        print(e)
        return None


def arp(options=None):
    options = options or []
    cmd = ['arp'] + options
    return [x.decode('utf-8') for x in subprocess.check_output(cmd).split(b'\n')[1:-1]]


def is_ip(x):
    parts = x.split('.')
    if len(parts) < 4:
        return False
    for part in parts:
        try:
            value = int(part)
        except ValueError:
            return False
        if not (0 <= value <= 255):
            return False
    return True


if __name__ == '__main__':
    try:
        sys.exit(main() or 0)
    except Exception as e:
        print(e, file=sys.stderr)
        print('{}')
        sys.exit(1)

#!/usr/bin/env python
# to run from hxat syslog do:
# grep CONNECT syslog | <this_script.py> > output.dat
#

import contextlib
import sys


# from http://stackoverflow.com/a/29824059
@contextlib.contextmanager
def _smart_open(filename, mode='Ur'):
    if filename == '-':
        if mode is None or mode == '' or 'r' in mode:
            fh = sys.stdin
        else:
            fh = sys.stdout
    else:
        fh = open(filename, mode)

    try:
        yield fh
    finally:
        if filename is not '-':
            fh.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        args = sys.argv[1]
    else:
        args = '-'

    with _smart_open(args) as handle:
        content = handle.read()

    i = 0
    dat = {}
    for line in content.splitlines():
        items = line.split()
        if len(items) < 3:
            continue  # skip if not a request log line

        if items[2] == '200':
            value = [1, 0]
        elif items[2] == '500':
            value = [0, 1]

        (h, m, s) = items[0].split(':')
        key = '{}:{}'.format(h, m)
        if key not in dat:
            dat[key] = value
        else:
            v = [ dat[key][0]+value[0], dat[key][1]+value[1] ]
            dat[key] = v

    sorted_ts = sorted(dat)
    for x in sorted_ts:
        print('{} {} {}'.format(x, dat[x][0], dat[x][1]))


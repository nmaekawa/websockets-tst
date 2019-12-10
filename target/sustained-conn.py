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


        repeated = items[7] if 'message repeated' in line else '1'
        if 'WSCONNECTING' in line:
            value = int(repeated)
        elif 'WSDISCONNECT' in line:
            value = -1 * int(repeated)
        else:
            i += 1

        if items[2] not in dat:
            dat[items[2]] = value
        else:
            dat[items[2]] += value

    print('IGNORED {} lines'.format(i))
    sorted_ts = sorted(dat)
    total = 0
    for x in sorted_ts:
        total += dat[x]
        print('{} {} {}'.format(x, dat[x], total))


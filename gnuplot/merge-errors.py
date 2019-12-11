#!/usr/bin/env python
# to get input files for this script:
# grep 'reset by peer' error.log | cut -d ' ' -f  2 | uniq -c > error-resetByPeer.dat
# grep 'premature' error.log | cut -d ' ' -f  2 | uniq -c > error-resetByPeer.dat
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
    if len(sys.argv) <= 2:
        print('missing input files')
        exit(1)

    with open(sys.argv[1], 'r') as f1:
        content1 = f1.read()
    with open(sys.argv[2], 'r') as f2:
        content2 = f2.read()

    i = 0
    dat = {}
    for line in content1.splitlines():
        items = line.split()
        dat[items[1]] = int(items[0])

    for line in content2.splitlines():
        items = line.split()
        if items[1] in dat:
            dat[items[1]] += int(items[0])
        else:
            dat[items[1]] = int(items[0])

    sorted_ts = sorted(dat)
    total = 0
    for x in sorted_ts:
        total += dat[x]
        print('{} {} {}'.format(x, dat[x], total))


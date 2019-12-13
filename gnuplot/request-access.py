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

        # get datetime
        (dmy, h, m, s) = items[3].split(':')
        key = '{}:{}:{}'.format(h, m, s)
        value = [0, 0, 0, 0]

        # is it http request?
        if '/annotation_store/api/' in items[6]:
            if items[8] == '200':
                value = [1, 0, 0, 0]
            else:
                value = [0, 1, 0, 0]

        # is it ws request?
        if '/ws/notification/' in items[6]:
            if items[8] == '101':
                value = [0, 0, 1, 0]
            else:
                value = [0, 0, 0, 1]


        if key not in dat:
            dat[key] = value
        else:
            v = [ dat[key][0]+value[0], dat[key][1]+value[1], dat[key][2]+value[2], dat[key][3]+value[3] ]
            dat[key] = v

    sorted_ts = sorted(dat)
    for x in sorted_ts:
        print('{} {} {} {} {}'.format(x, dat[x][0], dat[x][1], dat[x][2], dat[x][3]))


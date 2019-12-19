#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import contextlib
import jinja2
import os
import re
import sys

# current dir
THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def do_access_log(content):
    dat = {}
    for line in content.splitlines():
        items = line.split()

        # get datetime
        (dmy, h, m, s) = items[3].split(':')
        #key = '{}:{}:{}'.format(h, m, s)
        key = '{}:{}'.format(h, m)
        # TODO: ?need to go over replace 0:None?
        value = {
                'http_success': 0,
                'http_failure': 0,
                'ws_success': 0,
                'ws_failure': 0,
        }

        # is it http request?
        if '/annotation_store/api/' in items[6]:
            if items[8] == '200':
                value['http_success'] = 1
            else:
                value['http_failure'] = 1

        # is it ws request?
        if '/ws/notification/' in items[6]:
            if items[8] == '101':
                value['ws_success'] = 1
            else:
                value['ws_failure'] = 1

        if key not in dat:
            dat[key] = value
        else:
            dat[key]['http_success'] += value['http_success']
            dat[key]['http_failure'] += value['http_failure']
            dat[key]['ws_success'] += value['ws_success']
            dat[key]['ws_failure'] += value['ws_failure']

    sorted_ts = sorted(dat)  # returns a sorted list of keys
    dataset = {
            'x_labels': [], 'http_success': [], 'http_failure': [],
            'ws_success': [], 'ws_failure': [],
    }
    for ts in sorted_ts:
        dataset['x_labels'].append(ts)
        dataset['http_success'].append(dat[ts]['http_success'])
        dataset['http_failure'].append(dat[ts]['http_failure'])
        dataset['ws_success'].append(dat[ts]['ws_success'])
        dataset['ws_failure'].append(dat[ts]['ws_failure'])

    return dataset

def do_cron_log(content):
    dat = {}
    for line in content.splitlines():
        items = line.split()

        # get datetime
        (h, m, s) = items[1].split(':')
        key = '{}:{}'.format(h, m)
        value = {
                'nginx_nofiles': int(items[2]),
                'daphne_nofiles': int(items[3]),
                'total_nofiles': int(items[4]),
                'total_mem_used': int(items[5]),
        }

        if key not in dat:
            dat[key] = value
        else:
            dat[key]['nginx_nofiles'] += int(value['nginx_nofiles'])
            dat[key]['daphne_nofiles'] += int(value['daphne_nofiles'])
            dat[key]['total_nofiles'] += int(value['total_nofiles'])
            dat[key]['total_mem_used'] += int(value['total_mem_used'])

    sorted_ts = sorted(dat)  # returns a sorted list of keys
    dataset = {
            'x_labels': [], 'nginx_nofiles': [], 'daphne_nofiles': [],
            'total_nofiles': [], 'total_mem_used': [],
    }
    for ts in sorted_ts:
        dataset['x_labels'].append(ts)
        dataset['nginx_nofiles'].append(dat[ts]['nginx_nofiles'])
        dataset['daphne_nofiles'].append(dat[ts]['daphne_nofiles'])
        dataset['total_nofiles'].append(dat[ts]['total_nofiles'])
        dataset['total_mem_used'].append(dat[ts]['total_mem_used'])

    return dataset


def do_hxat_log(content):
    dat = {}
    for line in content.splitlines():
        items = line.split()

        # get datetime
        (h, m, s) = items[2].split(':')
        key = '{}:{}'.format(h, m)

        repeated = items[7] if 'message repeated' in line else '1'
        if 'WSCONNECT ' in line:
            value = int(repeated)
        elif 'WSDISCONNECT' in line:
            value = -1 * int(repeated)
        else:
            value = 0

        if key not in dat:
            dat[key] = value
        else:
            dat[key] += value

    sorted_ts = sorted(dat)
    dataset = {
            'x_labels': [], 'ws_conn': [], 'total': [],
    }
    total = 0
    for ts in sorted_ts:
        total += dat[ts]
        dataset['x_labels'].append(ts)
        dataset['ws_conn'].append(dat[ts])
        dataset['total'].append(total)

    return dataset

def do_responsetime_log(content):
    dat = {}
    for line in content.splitlines():
        items = line.split()

        # get datetime
        (dmy, h, m, s) = items[3].split(':')
        key = '{}:{}:{}'.format(h, m, s)

        response_times = re.findall(r'\[(.*)\]', items[-1])
        (r, u, sr) = response_times[0].split('|')
        request = float(r) if r != '-' else 0.0
        upstream = float(u) if u != '-' else 0.0
        selfreported = float(sr) if sr != '-' else 0.0
        value = {
                'request_time': request,
                'upstream_time': upstream,
                'selfreported_time': selfreported,
        }
        if key not in dat:
            dat[key] = value  # ignore multiple data points for same sec

    sorted_ts = sorted(dat)
    dataset = {
            'x_labels': [], 'request_time': [],
            'upstream_time': [], 'selfreported_time': [],
    }
    for ts in sorted_ts:
        dataset['x_labels'].append(ts)
        dataset['request_time'].append(dat[ts]['request_time'])
        dataset['upstream_time'].append(dat[ts]['upstream_time'])
        dataset['selfreported_time'].append(dat[ts]['selfreported_time'])

    return dataset

#
# configuration
#
config = {
    'http_ws': {
        'title': 'http vs ws requests',
        'data_masseuse': do_access_log,
        'input_filename': 'access.log',
        'template_name': 'http-ws-stackedbar.html',
        'output_filename': 'plot-http-ws-stacket-chart.html',
    },
    'nofiles': {
        'title': 'open files',
        'data_masseuse': do_cron_log,
        'input_filename': 'cron.log',
        'template_name': 'nofiles.html',
        'output_filename': 'plot-nofiles.html',
    },
    'wsconn': {
        'title': 'ws connections',
        'data_masseuse': do_hxat_log,
        'input_filename': 'syslog',
        'template_name': 'wsconn.html',
        'output_filename': 'plot-wsconn.html',
    },
    'responsetime': {
        'title': 'response time',
        'data_masseuse': do_responsetime_log,
        'input_filename': 'access.log',
        'template_name': 'responsetime.html',
        'output_filename': 'plot-responsetime.html',
    },

}

@click.command()
@click.option(
        '--workdir', default='/tmp', show_default=True,
        help='dir where data logs are, where output is written to',)
@click.option(
        '--chart', default='http_ws', show_default=True,
        multiple=True,  # can be repeated multiple times
        type=click.Choice(
            config.keys(),
            case_sensitive=False),
        help='type of chart to be produced',)
def cli(workdir, chart=('http_ws')):
    templates_dir = os.path.join(THIS_DIR, 'templates')
    j2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            trim_blocks=True,
            )

    for chart_type in chart:
        # read file and get dataset
        input_filepath = os.path.join(
                workdir, config[chart_type]['input_filename'])
        with open(input_filepath, 'r') as fd:
            content = fd.read()
        dataset = config[chart_type]['data_masseuse'](content)

        html = j2_env.get_template(
                config[chart_type]['template_name']).render(
                        dat=dataset)

        output_filepath = os.path.join(
                workdir, config[chart_type]['output_filename'])
        with open(output_filepath, 'w') as handle:
            handle.write(html)



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



if __name__ == '__main__':
    sys.exit(cli())  #pragma: no cover




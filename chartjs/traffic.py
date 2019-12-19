#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import contextlib
import datetime
import glob
import jinja2
import os
import re
import sys

# current dir
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
month_by_name = ['na', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
        'Sep', 'Oct', 'Nov', 'Dec']


def do_access_log(content, dataset,freq='hourly'):
    for line in content.splitlines():
        items = line.split()

        # get datetime
        date = datetime.datetime.strptime(items[3][1:], '%d/%b/%Y:%H:%M:%S')
        if freq == 'daily':
            date2 = date.replace(hour=0, minute=0, second=0)
        else:
            date2 = date.replace(minute=0, second=0)
        key = date2.isoformat()

        # datapoint
        value = {
                'success': 0,
                'failure': 0,
                'rtime_max': 0,
                'rtime_min': 0,
                'rtime_avg': 0,
        }

        # request time
        request_times = re.findall(r'\[(.*)\]', items[-1])
        (r, u, sr) = request_times[0].split('|')
        request = float(r) if r != '-' else 0.0
        value['rtime_max'] = value['rtime_min'] = value['rtime_avg'] = request

        # success?
        status = items[8]
        if status[0] == '2' or status[0] == '3':
            value['success'] = 1
        else:
            value['failure'] = 1

        if key not in dataset:
            dataset[key] = value
        else:
            dataset[key]['success'] += value['success']
            dataset[key]['failure'] += value['failure']
            if dataset[key]['rtime_max'] < value['rtime_max']:
                dataset[key]['rtime_max'] = value['rtime_max']
            if dataset[key]['rtime_min'] > value['rtime_min']:
                dataset[key]['rtime_min'] = value['rtime_min']
            dataset[key]['rtime_avg'] = \
                    (dataset[key]['rtime_max'] + dataset[key]['rtime_min'])/2


    return dataset



#
# configuration
#
config = {
    'traffic': {
        'title': 'http vs ws requests',
        'data_masseuse': do_access_log,
        'input_filename': 'access.log',
        'template_name': 'traffic.html',
        'output_filename': 'plot-traffic.html',
    },

}

@click.command()
@click.option(
        '--workdir', default='/tmp', show_default=True,
        help='dir where data logs are, where output is written to',)
@click.option(
        '--chart', default='traffic', show_default=True,
        type=click.Choice(
            config.keys(),
            case_sensitive=True),
        help='type of chart to be produced',)
@click.option(
        '--freq', default='hourly', show_default=True,
        type=click.Choice(
            ['hourly', 'daily'],
            case_sensitive=True),
        help='aggregate data daily, hourly, ...',)
def cli(workdir, chart='traffic', freq='hourly'):
    templates_dir = os.path.join(THIS_DIR, 'templates')
    j2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            trim_blocks=True,
            )

    dataset = {}
    filename_patt = os.path.join(
            workdir, config[chart]['input_filename'] + '*')
    for filename in glob.glob(filename_patt):
        # read file and get dataset
        with open(filename, 'r') as fd:
            content = fd.read()
        one_set = config[chart]['data_masseuse'](content, dataset, freq)

    sorted_ts = sorted(dataset)  # returns a sorted list of keys
    result = {
            'x_labels': [], 'success': [], 'failure': [],
            'rtime_max': [], 'rtime_min': [], 'rtime_avg': [],
    }
    for ts in sorted_ts:
        result['x_labels'].append(ts)
        result['success'].append(dataset[ts]['success'])
        result['failure'].append(dataset[ts]['failure'])
        result['rtime_max'].append(dataset[ts]['rtime_max'])
        result['rtime_min'].append(dataset[ts]['rtime_min'])
        result['rtime_avg'].append(dataset[ts]['rtime_avg'])

    print(
            'x_labels({}), success({}), failure({}), rtime_max({}), rtime_min({}), rtime_avg({})'.format(
                len(result['x_labels']),
                len(result['success']),
                len(result['failure']),
                len(result['rtime_max']),
                len(result['rtime_min']),
                len(result['rtime_avg']),
                )
            )

    # print template
    html = j2_env.get_template(
            config[chart]['template_name']).render(
                    dat=result)

    output_filepath = os.path.join(
            workdir, config[chart]['output_filename'])
    with open(output_filepath, 'w') as handle:
        handle.write(html)





if __name__ == '__main__':
    sys.exit(cli())  #pragma: no cover




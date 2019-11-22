#
# automated run: use --no-web and --csv
# $> locust -f examples/basic.py --csv=example --no-web -t10m -c 1 -r 1 --host <hxat url>
#
import os

import json
import logging
from random import randint
from subprocess import Popen
from subprocess import PIPE
from uuid import uuid4

from locust import between
from locust import HttpLocust
from locust import TaskSet
from locust import task
import locust.stats

# set custom interval for stats; default is 2s
locust.stats.CSV_STATS_INTERVAL_SEC = 5

TOKEN = ''
USER_ID = ''
USER_NAME = ''
CONTEXT_ID = ''
COLLECTION_ID = ''
TARGET_SOURCE_ID = ''
RESOURCE_LINK_ID = ''
UTM_SOURCE = ''

# this is particular to the target_source document
# and used to randomize the region being annotate
PTAG=2
target_doc = [0, 589, 313, 434, 593, 493]


def fetch_fortune():
    process = Popen('fortune', shell=True, stdout=PIPE, stderr=None)
    output, _ = process.communicate()
    return output.decode('utf-8')

def fresh_wa():
    sel_start = randint(0, target_doc[PTAG])
    sel_end = randint(sel_start, target_doc[PTAG])
    x = {
        "@context": "http://catchpy.harvardx.harvard.edu.s3.amazonaws.com/jsonld/catch_context_jsonld.json",
        "body": {
            "type": "List",
            "items": [{
                "format": "text/html",
                "language": "en",
                "purpose": "commenting",
                "type": "TextualBody",
                "value": fetch_fortune()
            }],
        },
        "creator": {
            "id": "d99019cf42efda58f412e711d97beebe",
            "name": "nmaekawa2017"
        },
        "id": "013ec74f-1234-5678-3c61-b5cf9d6f7484",
        "permissions": {
            "can_admin": [ USER_ID ],
            "can_delete": [ USER_ID ],
            "can_read": [],
            "can_update": [ USER_ID ]
        },
        "platform": {
            "collection_id": COLLECTION_ID,
            "context_id": CONTEXT_ID,
            "platform_name": "edX",
            "target_source_id": TARGET_SOURCE_ID,
        },
        "schema_version": "1.1.0",
        "target": {
            "items": [{
                "selector": {
                    "items": [
                        { "endSelector": { "type": "XPathSelector", "value": "/div[1]/p[{}]".format(PTAG) },
                            "refinedBy": { "end": sel_end, "start": sel_start, "type": "TextPositionSelector" },
                            "startSelector": { "type": "XPathSelector", "value": "/div[1]/p[{}]".format(PTAG) },
                            "type": "RangeSelector" },
                    ],
                    "type": "Choice"
                },
                "source": "http://sample.com/fake_content/preview", "type": "Text"
            }],
            "type": "List"
        },
        "type": "Annotation"
    }
    return x

class UserBehavior_CreateWebAnnotation(TaskSet):
    #def on_start(self):
    #    self.catcha = fresh_wa()

    @task(1)
    def add_annotation(self):
        catcha = fresh_wa()

        # create annotation
        anno_id = str(uuid4())
        target_path = '/annotation_store/api/{}?resource_link_id={}&utm_source={}&version=catchpy'.format(
                anno_id, RESOURCE_LINK_ID, UTM_SOURCE)
        response = self.client.post(
            target_path, json=catcha, catch_response=True,
            headers={
                'Content-Type': 'Application/json',
                'x-annotator-auth-token': TOKEN,
                'Referer': 'https://naomi.hxat.hxtech.org/lti_init/launch_lti/',
            },
            verify=False,
        )
        if response.content == '':
            response.failure('no data')
        else:
            try:
                a_id = response.json()['id']
            except KeyError:
                resp = response.json()
                if 'payload' in resp:
                    response.failure(resp['payload'])
                else:
                    response.failure('no id in response')
                return
            except json.decoder.JSONDecodeError as e:
                response.failure(e)
                return
            else:
                response.success()


class WebsiteUser(HttpLocust):
    task_set = UserBehavior_CreateWebAnnotation
    wait_time = between(5, 20)








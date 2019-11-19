import os

from copy import deepcopy
import json
from random import randint
import logging
from uuid import uuid4

from locust import between
from locust import HttpLocust
from locust import TaskSet
from locust import task

TOKEN = ''
USER_ID = ''
USER_NAME = ''
CONTEXT_ID = ''
COLLECTION_ID = ''
RESOURCE_LINK_ID = ''
UTM_SOURCE = ''


def wa_template():
    x = {
        "@context": "http://catchpy.harvardx.harvard.edu.s3.amazonaws.com/jsonld/catch_context_jsonld.json",
        "body": {
            "type": "List",
            "items": [{
                "format": "text/html",
                "language": "en",
                "purpose": "commenting",
                "type": "TextualBody",
                "value": [ "naominaominaomi" ]
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
            "target_source_id": "1"
        },
        "schema_version": "1.1.0",
        "target": {
            "items": [{
                "selector": {
                    "items": [
                        { "endSelector": { "type": "XPathSelector", "value": "/div[1]/p[2]" },
                            "refinedBy": { "end": 7, "start": 0, "type": "TextPositionSelector" },
                            "startSelector": { "type": "XPathSelector", "value": "/div[1]/p[2]" },
                            "type": "RangeSelector" },
                        { "end": 732, "start": 725, "type": "TextPositionSelector" },
                        { "exact": "Biltong", "prefix": "", "suffix": " turducken swine, shoulder alcatra ",
                            "type": "TextQuoteSelector" }
                    ],
                    "type": "Choice"
                },
                "source": "http://sample.com/fake_content/preview", "type": "Text"
            }],
            "type": "List"
        },
        "type": "Annotation"
    }
    return deepcopy(x)

class UserBehavior_CreateWebAnnotation(TaskSet):
    def on_start(self):
        self.catcha = wa_template()

    @task(1)
    def add_annotation(self):
        # set user
        user = self.catcha['creator']['id']
        # generate token for user
        token = TOKEN

        # create annotation
        anno_id = str(uuid4())
        target_path = '/annotation_store/api/{}?resource_link_id={}&utm_source={}&version=catchpy'.format(
                anno_id, RESOURCE_LINK_ID, UTM_SOURCE)
        response = self.client.post(
            target_path, json=self.catcha, catch_response=True,
            headers={
                'Content-Type': 'Application/json',
                'x-annotator-auth-token': token,
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
    wait_time = between(2, 30)








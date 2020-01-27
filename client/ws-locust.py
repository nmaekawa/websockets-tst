#
# ws heavily based on
# https://github.com/websocket-client/websocket-client/blob/master/bin/wsdump.py
#
import code
import gevent
import json
import jwt
import os
import re
import ssl
import sys
import threading
import time

from datetime import datetime
from dateutil import tz
from random import randint
from subprocess import Popen
from subprocess import PIPE
from uuid import uuid4

from locust import between
from locust import constant
from locust import events
from locust import HttpLocust
from locust import Locust
from locust import seq_task
from locust import task
from locust import TaskSequence
from locust import TaskSet
from locust import ResponseError
from lti import ToolConsumer

import websocket


#info from environment
#---------------------
USER_ID = os.environ.get('USER_ID', 'fake_user_id')
USER_NAME = os.environ.get('USER_NAME', 'fake_user_name')
CONTEXT_ID = os.environ.get('CONTEXT_ID', 'fake_context_id')
COLLECTION_ID = os.environ.get('COLLECTION_ID', 'fake_collection_id')
TARGET_SOURCE_ID = os.environ.get('TARGET_SOURCE_ID', '0')
RESOURCE_LINK_ID = os.environ.get('RESOURCE_LINK_ID', 'fake_resource_link_id')

VERBOSE = os.environ.get('WS_TEST_VERBOSE', 'true').lower() == 'true'

# this is particular to the target_source document
# and used to randomize the region being annotate
PTAG=2
target_doc = [0, 589, 313, 434, 593, 493]

# valid codes for ws read
OPCODE_DATA = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)
websocket.enableTrace(True)

class Console(code.InteractiveConsole):
    def write(self, data):
        sys.stdout.write("\033[2K\033[E")
        sys.stdout.write("\033[34m< " + data + "\033[39m")
        sys.stdout.write("\n> ")
        sys.stdout.flush()


class SocketClient(object):
    '''hxat websockets client

    connects and reads from ws; does not send anything; ever.
    '''
    def __init__(self, host, app_url_path='', timeout=2):
        self.console = Console()
        self.verbose = VERBOSE
        self.host = host
        self.session_id = uuid4().hex
        self.protocol = 'wss'
        path = os.path.join('/', app_url_path)
        self.url = '{}://{}{}/'.format(self.protocol, host, path)
        self.ws = None
        self.ws_timeout = timeout
        self.thread = None

        events.quitting += self.on_close

    def log(self, msg):
        if self.verbose:
            self.console.write(msg)


    def connect(self):
        if self.ws is None:
            self.ws = websocket.create_connection(
                    url=self.url,
                    sslopt={
                        'cert_reqs': ssl.CERT_NONE,  # do not check certs
                        'check_hostname': False,     # do not check hostname
                        }
                    )
            # if server closes the connection, the thread dies, but
            # if thread dies, it closes the connection?
            self.thread = threading.Thread(
                    target=self.recv,
                    daemon=True
                    )
            self.thread.start()
        else:
            self.log('{}| nothing to do: already connected'.format(
                self.session_id))


    def close(self):
        if self.ws is not None:
            self.ws.close()
        else:
            self.log('{}| nothing to do: NOT connected'.format(
                self.session_id))

    def on_close(self):
        self.close()


    def _recv(self):
        try:
            frame = self.ws.recv_frame()
        except websocket.WebSocketException:
            return websocket.ABNF.OPCODE_CLOSE, None

        if not frame:
            return 0xb, None  # invented code for invalid frame
        elif frame.opcode in OPCODE_DATA:
            return frame.opcode, frame.data
        elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
            # server closed ws connection
            self.ws.send_close()
            return frame.opcode, None
        elif frame.opcode == websocket.ABNF.OPCODE_PING:
            self.ws.pong(frame.data)
            return frame.opcode, frame.data

        return frame.opcode, frame.data


    def recv(self):
        while True:
            opcode, data = self._recv()

            if opcode == websocket.ABNF.OPCODE_TEXT and isinstance(
                    data, bytes):
                data = str(data, 'utf-8')
                # success
                response_length = self.calc_response_length(data)
                events.request_success.fire(
                    request_type='ws-recv', name='receive',
                    response_time=None,
                    response_length=response_length)

            elif opcode == websocket.ABNF.OPCODE_BINARY:
                # failure: don't understand binary
                events.request_failure.fire(
                    request_type='ws-recv', name='receive',
                    response_time=None,
                    exception=websocket.WebSocketException(
                        'Unexpected binary frame'),
                    )

            elif opcode == 0xb:
                # failure: invalid frame
                events.request_failure.fire(
                    request_type='ws-recv', name='receive',
                    response_time=None,
                    exception=websocket.WebSocketException(
                        'Invalid frame'),
                    )

            elif opcode == websocket.ABNF.OPCODE_CLOSE:
                self.log(
                        '{}| ####################### recv CLOSE'.format(
                            self.session_id))
                break  # terminate loop

            elif opcode == websocket.ABNF.OPCODE_PING:
                # ignore ping-pong
                self.log(
                        '{}| *********************** ping'.format(
                            self.session_id))
                pass

            else:
                # failure: unknown
                events.request_failure.fire(
                    request_type='ws-recv', name='receive',
                    response_time=None,
                    exception=websocket.WebSocketException(
                        '{}| Unknown error for opcode({})'.format(
                            self.session_id, opcode)),
                    )

            self.log('{}| *********************** recv ({}) ({})'.format(
                self.session_id, opcode, data))


    def calc_response_length(self, response):
        length = 0
        json_data = json.dumps(response)
        return len(json_data)


######################################################
# http hxat operations:
#   lti login
#   get static pages (hxighlighter javascripts and css)
#   search annotations
#   create annotation
######################################################

def make_jwt(
    apikey, secret, user,
    iat=None, ttl=36000, override=[],
    backcompat=False):
    payload = {
        'consumerKey': apikey if apikey else str(uuid4()),
        'userId': user if user else str(uuid4()),
        'issuedAt': iat if iat else datetime.now(tz.tzutc()).isoformat(),
        'ttl': ttl,
    }
    if not backcompat:
        payload['override'] = override

    return jwt.encode(payload, secret)


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

def hxat_create(locust):
    catcha = fresh_wa()

    # create annotation
    anno_id = str(uuid4())
    params = {
            'resource_link_id': RESOURCE_LINK_ID,
            'utm_source': locust.cookies['UTM_SOURCE'],
            'version': 'catchpy',
            }
    target_path = '/annotation_store/api/{}?'.format(anno_id)
    response = locust.client.post(
        target_path, json=catcha, catch_response=True,
        name='/annotation_store/api/create',
        headers={
            'Content-Type': 'Application/json',
            'x-annotator-auth-token': locust.store_token,
            'Referer': 'https://naomi.hxat.hxtech.org/lti_init/launch_lti/',
        },
        params=params,
        verify=locust.verify,
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


def hxat_search(locust, limit=50, offset=0):
    params = {
            'resource_link_id': RESOURCE_LINK_ID,
            'utm_source': locust.cookies['UTM_SOURCE'],
            'version': 'catchpy',
            'limit': limit,
            'offset': offset,
            'media': 'text',
            'source_id': TARGET_SOURCE_ID,
            'context_id': CONTEXT_ID,
            'collection_id': COLLECTION_ID,
            }
    target_path = '/annotation_store/api/'
    response = locust.client.get(
            target_path, catch_response=True,
            name='/annotation_store/api/search',
            headers={
                'Content-Type': 'Application/json',
                'x-annotator-auth-token': locust.store_token,
                'Referer': 'https://naomi.hxat.hxtech.org/lti_init/launch_lti/',
            },
            params=params,
            verify=locust.verify,
    )
    if response.content == '':
        response.failure('no data')
    else:
        try:
            rows = response.json()['rows']
        except KeyError:
            resp = response.json()
            if 'payload' in resp:
                response.failure(resp['payload'])
            else:
                response.failure('missing rows in search response')
            return
        except json.decoder.JSONDecodeError as e:
            response.failure(e)
            return
        else:
            response.success()

def hxat_get_static(locust, url_path):
    target_path = os.path.join('/static/', url_path)
    response = locust.client.get(
            target_path, catch_response=True,
            cookies=locust.cookies,
            name='/static',
            headers={
                'Accept': 'text/css,*/*;q=0.1',
                'Referer': 'https://naomi.hxat.hxtech.org/lti_init/launch_lti/',
            },
            verify=locust.verify,
    )
    if response.content == '':
        response.failure('no data')
    else:
        response.success()


def hxat_lti_launch(locust):

    target_path = '/lti_init/launch_lti/'
    consumer = ToolConsumer(
            consumer_key=os.environ.get('HXAT_CONSUMER', 'fake_consumer_key'),
            consumer_secret=os.environ.get('HXAT_SECRET', 'fake_secret_key'),
            launch_url='{}{}'.format(locust.host, target_path),
            params={
                "lti_message_type": "basic-lti-launch-request",
                "lti_version": "LTI-1p0",
                "resource_link_id": RESOURCE_LINK_ID,
                "lis_person_sourcedid": os.environ.get('LIS_PERSON_SOURCEDID','fake_person'),
                "lis_outcome_service_url": os.environ.get('LIS_OUTCOME_SERVICE_URL', 'fake_url'),
                "user_id": USER_ID,
                "roles": os.environ.get('USER_ROLES', 'fake_role'),
                "context_id": CONTEXT_ID,
                },
            )
    headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            }
    params = consumer.generate_launch_data()
    locust.console.write('LTI LTI LTI LTI LTI: {}'.format(params))
    response = locust.client.post(
            target_path, catch_response=True,
            name='/lti_launch/', headers=headers, data=params,
            verify=locust.verify,
            )
    if response.content == '':
        response.failure('no data')
    else:
        locust.console.write('-------------------------------------------- response cookies ({})'.format(response.cookies))
        cookie_csrf = response.cookies.get('csrftoken', None)
        cookie_sid = response.cookies.get('sessionid', None)
        if not cookie_csrf or not cookie_sid:
            response.failure('missing csrf and/or session-id cookies')
            return False
        else:
            locust.cookies['UTM_SOURCE'] = cookie_sid
            locust.cookies['CSRF_TOKEN'] = cookie_csrf
            response.success()
            return True


class WSBehavior(TaskSet):
    wait_time = between(60, 300)
    def on_start(self):
        # basic lti login for hxat text annotation
        ret = hxat_lti_launch(self.locust)
        if ret:
            hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.css')
            hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.js')
            hxat_search(self.locust)
            self.locust.ws_client.connect()
        else:
            raise Exception('failed to lti login')

    def on_stop(self):
        if self.locust.ws_client is not None:
            self.locust.ws_client.log(
                    '========================================================= closing ws')
            self.locust.ws_client.close()


    @task(1)
    def lurker1(self):
        hxat_search(
                locust=self.locust,
                limit=randint(10, 50),
                offset=randint(50, 200),
                )

    @task(10)
    def lurker2(self):
        hxat_search(
                locust=self.locust,
                )

    @task(1)
    def homework1(self):
        hxat_create(self.locust)
        hxat_search(self.locust)




class WSUser(HttpLocust):
    task_set = WSBehavior

    def __init__(self, *args, **kwargs):
        super(WSUser, self).__init__(*args, **kwargs)

        self.console = Console()
        self.cookies = dict()  # csrf, session after lti-login
        self.store_token = make_jwt(
                apikey=os.environ.get('STORE_CONSUMER', 'fake_consumer'),
                secret=os.environ.get('STORE_SECRET', 'fake_secret'),
                user=USER_ID
                )
        # remove protocol from url so we can do wss requests
        (proto, hostname) = self.host.split('//')
        url_path = '/ws/notification/{}--{}--{}'.format(
                re.sub('[\W_]', '-', CONTEXT_ID),
                re.sub('[\W_]', '-', COLLECTION_ID),
                TARGET_SOURCE_ID
                )
        self.ws_client = SocketClient(hostname, app_url_path=url_path)

        # check if self-signed certs
        if 'hxtech.org' in hostname:
            self.verify = os.environ.get('REQUESTS_CA_BUNDLE', False)
        else:
            self.verify = True




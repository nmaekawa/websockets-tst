#
# original from
#
import code
import gevent
import json
import os
import re
import ssl
import sys
import threading
import time

from random import randint
from subprocess import Popen
from subprocess import PIPE
from uuid import uuid4

from locust import HttpLocust, TaskSet, task, ResponseError, events, Locust
import websocket


#info for naomi.hxat.hxtech.org
#---------------------------------------
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
    def __init__(self, host, app_url_path='', timeout=2):
        self.console = Console()
        self.host = host
        self.session_id = uuid4().hex
        self.protocol = 'wss'
        path = os.path.join('/', app_url_path)
        self.url = '{}://{}{}/'.format(self.protocol, host, path)
        self.ws_timeout = timeout

        events.quitting += self.on_close
        self.console.write('*********************** connecting to {}'.format(self.url))
        self.connect()


    def connect(self):
        self.ws = websocket.create_connection(
                url=self.url,
                sslopt={
                    'cert_reqs': ssl.CERT_NONE,  # do not check certs
                    'check_hostname': False,     # do not check hostname
                    }
                )

        self.thread = threading.Thread(target=self.recv_ws)
        self.thread.daemon = True
        self.thread.start()


    def on_close(self):
        self.ws.close()


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


    def recv_ws(self):
        while True:
            self.console.write('*********************** recv loop')
            #start_time = time.time()
            opcode, data = self._recv()
            #elapsed = int((time.time() - start_time) * 1000)

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
                # try to connect again?
                self.console.write('####################### recv CLOSE')
                break

            elif opcode == websocket.ABNF.OPCODE_PING:
                # ignore ping-pong
                self.console.write('*********************** ping')
                pass

            else:
                # failure: unknown
                events.request_failure.fire(
                    request_type='ws-recv', name='receive',
                    response_time=None,
                    exception=websocket.WebSocketException(
                        'Unknown error for opcode({})'.format(opcode)),
                    )

            self.console.write('*********************** recv ({}) ({})'.format(opcode, data))


    def calc_response_length(self, response):
        length = 0
        json_data = json.dumps(response)
        return len(json_data)
        '''
        for r in response:
            json_data = json.dumps(r)
            length += len(json_data)
        return length
        '''



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

class WSBehavior(TaskSet):

    @task(10)
    def add_annotation(self):
        catcha = fresh_wa()

        # create annotation
        anno_id = str(uuid4())
        params = {
                'resource_link_id': RESOURCE_LINK_ID,
                'utm_source': UTM_SOURCE,
                'version': 'catchpy',
                }
        target_path = '/annotation_store/api/{}?'.format(anno_id)
        response = self.client.post(
            target_path, json=catcha, catch_response=True,
            name='/annotation_store/api/create',
            headers={
                'Content-Type': 'Application/json',
                'x-annotator-auth-token': TOKEN,
                'Referer': 'https://naomi.hxat.hxtech.org/lti_init/launch_lti/',
            },
            params=params,
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


class WSUser(HttpLocust):
    task_set = WSBehavior
    min_wait = 60
    max_wait = 600

    def __init__(self, *args, **kwargs):
        super(WSUser, self).__init__(*args, **kwargs)

        (proto, hostname) = self.host.split('//')
        url_path = '/ws/notification/{}--{}--{}'.format(
                re.sub('[\W_]', '-', CONTEXT_ID),
                re.sub('[\W_]', '-', COLLECTION_ID),
                TARGET_SOURCE_ID
                )
        self.ws_client = SocketClient(hostname, app_url_path=url_path)





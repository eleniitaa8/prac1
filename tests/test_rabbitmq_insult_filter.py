# tests/test_rabbitmq_insult_filter.py
import os
import sys
# Añadimos la raíz del proyecto al path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root)

import pytest
import multiprocessing
import time
import pika
import json
import uuid
from rabbitmq_impl.insult_service import service as srv_mod
from rabbitmq_impl.insult_filter.worker import worker

pytestmark = pytest.mark.filterwarnings(
    "ignore:.*isSet\\(\\) is deprecated.*:DeprecationWarning"
)

# helper RPC
def rpc_call(method, text=None):
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    res = ch.queue_declare('', exclusive=True)
    callback = res.method.queue
    corr_id = str(uuid.uuid4())
    payload = {'method': method}
    if text is not None:
        payload['text'] = text
    ch.basic_publish(
        exchange='',
        routing_key='insult_rpc_queue',
        properties=pika.BasicProperties(
            reply_to=callback,
            correlation_id=corr_id
        ),
        body=json.dumps(payload)
    )
    resp = None
    for _ in range(20):
        mf, props, body = ch.basic_get(callback, auto_ack=True)
        if body and props.correlation_id == corr_id:
            resp = json.loads(body)
            break
        time.sleep(0.1)
    conn.close()
    return resp

@pytest.fixture(scope='module', autouse=True)
def start_services():
    # 1) arrancar InsultService
    p1 = multiprocessing.Process(target=srv_mod.main)
    p1.start()
    time.sleep(1)
    # 2) arrancar FilterWorker
    p2 = multiprocessing.Process(target=worker)
    p2.start()
    time.sleep(0.5)
    yield
    for p in (p1, p2):
        p.terminate()
        p.join()

def test_filtering():
    # Intentamos añadir 'badword' (puede que ya exista si hay restos, no importa)
    r = rpc_call('add_insult', 'badword')
    assert r is not None and 'success' in r

    # Verificamos que realmente está en la lista
    r2 = rpc_call('get_insults')
    insults = r2.get('insults', [])
    assert 'badword' in insults

    # Encolamos la tarea de filtrado
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    ch.queue_declare(queue='filter_queue')
    ch.queue_declare(queue='filter_results_queue')
    text = 'hello badword world'
    ch.basic_publish(exchange='', routing_key='filter_queue', body=text)

    # Polling hasta que aparezca el resultado o 2s
    result = None
    deadline = time.time() + 2.0
    while time.time() < deadline:
        mf, props, body = ch.basic_get('filter_results_queue', auto_ack=True)
        if body:
            result = body.decode()
            break
        time.sleep(0.1)
    conn.close()

    assert result == 'hello CENSORED world'

# tests/test_rabbitmq_insult_service.py
import os, sys
# Insertar la carpeta padre (.. = prak1) en sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root)

import pytest, multiprocessing, time, pika, json, uuid
from rabbitmq_impl.insult_service import service as srv_mod

# Helper para RPC
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
    for _ in range(10):
        method_frame, props, body = ch.basic_get(callback, auto_ack=True)
        if body and props.correlation_id == corr_id:
            resp = json.loads(body)
            break
        time.sleep(0.1)
    conn.close()
    return resp

@pytest.fixture(scope='module', autouse=True)
def start_service():
    p = multiprocessing.Process(target=srv_mod.main)
    p.start()
    time.sleep(0.5)
    yield
    p.terminate(); p.join()

def test_add_and_list():
    r = rpc_call('add_insult', 'foo')
    assert r['success'] is True
    r = rpc_call('add_insult', 'foo')
    assert r['success'] is False
    r = rpc_call('get_insults')
    assert 'foo' in r['insults']

def test_broadcast():
    # nos suscribimos al fanout
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    ch.exchange_declare(exchange='insults_exchange', exchange_type='fanout')
    q = ch.queue_declare('', exclusive=True).method.queue
    ch.queue_bind(exchange='insults_exchange', queue=q)

    # añadimos un insulto y esperamos al menos un ciclo de broadcast
    rpc_call('add_insult', 'bar')
    time.sleep(1.5)

    # obtenemos la lista actual de insultos vía RPC
    r = rpc_call('get_insults')
    valid_insults = set(r.get('insults', []))

    # leemos mensajes hasta encontrar uno válido o agotarnos
    msg = None
    for _ in range(30):          # hasta 3 segundos
        mf, props, body = ch.basic_get(q, auto_ack=True)
        if body:
            candidate = body.decode()
            if candidate in valid_insults:
                msg = candidate
                break
        time.sleep(0.1)
    conn.close()

    assert msg in valid_insults

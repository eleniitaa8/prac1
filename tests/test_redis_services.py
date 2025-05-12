import pytest
import subprocess
import sys
import time
import os
import json
import uuid
import threading
import redis

@pytest.fixture(scope="module", autouse=True)
def start_services():
    # 1) chequeo Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    try:
        r.ping()
    except redis.ConnectionError as e:
        pytest.skip(f"Redis no responde en localhost:6379 – {e}")

    r.flushdb()

    # 2) lanzar servicios Redis
    # Añadir ruta del proyecto para localizar scripts
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    service_script = os.path.join(root, 'redis_impl', 'insult_service', 'service.py')
    filter_script = os.path.join(root, 'redis_impl', 'insult_filter', 'service.py')


    p1 = subprocess.Popen(
        [sys.executable, service_script, '--redis-host', 'localhost', '--redis-port', '6379'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    p2 = subprocess.Popen(
        [sys.executable, filter_script, '--redis-host', 'localhost', '--redis-port', '6379'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # 3) Polling readiness
    deadline = time.time() + 15
    ok1 = ok2 = False
    while time.time() < deadline and (not ok1 or not ok2):
        try:
            client_id = str(uuid.uuid4())
            resp_stream = f"insult_responses:{client_id}"
            req = {'command': 'get_insults', 'client_id': client_id}
            r.rpush('insult_requests', json.dumps(req))
            if r.blpop(resp_stream, timeout=1):
                ok1 = True
        except:
            pass

        try:
            client_id2 = str(uuid.uuid4())
            resp_stream2 = f"filter_responses:{client_id2}"
            req2 = {'text': 'hello', 'client_id': client_id2}
            r.rpush('filter_requests', json.dumps(req2))
            if r.blpop(resp_stream2, timeout=1):
                ok2 = True
        except:
            pass

        time.sleep(0.2)

    if not (ok1 and ok2):
        stderr1 = p1.stderr.read()
        stderr2 = p2.stderr.read()
        p1.kill()
        p2.kill()
        pytest.skip("Servicios Redis no arrancaron a tiempo:\n"
                    f"insult_service stderr:\n{stderr1}\n"
                    f"insult_filter stderr:\n{stderr2}")

    yield

    p1.terminate()
    p2.terminate()


def test_filtering():
    r = redis.Redis(decode_responses=True)
    # Añadir insulto
    client_id1 = str(uuid.uuid4())
    resp_stream1 = f"insult_responses:{client_id1}"
    req1 = {'command': 'add_insult', 'insult': 'badword', 'client_id': client_id1}
    r.rpush('insult_requests', json.dumps(req1))
    resp1 = json.loads(r.blpop(resp_stream1, timeout=5)[1])
    assert resp1['added'] is True

    # Filtrar texto
    time.sleep(0.1)
    client_id2 = str(uuid.uuid4())
    resp_stream2 = f"filter_responses:{client_id2}"
    req2 = {'text': 'hey badword', 'client_id': client_id2}
    r.rpush('filter_requests', json.dumps(req2))
    resp2 = json.loads(r.blpop(resp_stream2, timeout=5)[1])
    assert 'CENSORED' in resp2['filtered']


def test_add_and_list():
    r = redis.Redis(decode_responses=True)
    client_id = str(uuid.uuid4())
    resp_stream = f"insult_responses:{client_id}"

    # Prueba idempotencia
    req = {'command': 'add_insult', 'insult': 'foo', 'client_id': client_id}
    r.rpush('insult_requests', json.dumps(req))
    resp = json.loads(r.blpop(resp_stream, timeout=5)[1])
    assert resp['added'] is True

    r.rpush('insult_requests', json.dumps(req))
    resp2 = json.loads(r.blpop(resp_stream, timeout=5)[1])
    assert resp2['added'] is False

    # Listar insultos
    client_id2 = str(uuid.uuid4())
    resp_stream2 = f"insult_responses:{client_id2}"
    req_list = {'command': 'get_insults', 'client_id': client_id2}
    r.rpush('insult_requests', json.dumps(req_list))
    resp_list = json.loads(r.blpop(resp_stream2, timeout=5)[1])
    assert 'foo' in resp_list['insults']


def test_subscribe_and_broadcast(capsys):
    r = redis.Redis(decode_responses=True)

    def subscriber():
        pubsub = r.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe('insults_channel')
        for msg in pubsub.listen():
            print(f"[CB] {msg['data']}")
            break

    t = threading.Thread(target=subscriber, daemon=True)
    t.start()
    time.sleep(1)

    # Añadir insulto para desencadenar publish
    client_id = str(uuid.uuid4())
    req = {'command': 'add_insult', 'insult': 'test_sub', 'client_id': client_id}
    r.rpush('insult_requests', json.dumps(req))
    _ = r.blpop(f"insult_responses:{client_id}", timeout=5)

    time.sleep(0.1)
    captured = capsys.readouterr()
    assert '[CB]' in captured.out
import pytest, redis, multiprocessing, time
from redis_impl.insult_service.service import broadcaster

@pytest.fixture(scope='module')
def rds():
    r = redis.Redis()
    r.flushdb()
    return r

@pytest.fixture(scope='module', autouse=True)
def start_broadcaster(rds):
    # periodicidad rápida para tests
    p = multiprocessing.Process(target=broadcaster, args=(1.0,))
    p.start()
    time.sleep(0.1)
    yield
    p.terminate()
    p.join()


def test_add_and_list(rds):
    assert rds.sadd('insults', 'foo') == 1
    assert rds.sadd('insults', 'foo') == 0
    members = {x.decode() for x in rds.smembers('insults')}
    assert 'foo' in members


def test_broadcast(rds):
    pubsub = rds.pubsub()
    pubsub.subscribe('insults_channel')
    time.sleep(1.5)
    msg = None
    for _ in range(5):
        m = pubsub.get_message(timeout=0.5)
        if m and m['type']=='message':
            msg = m['data'].decode()
            break
    assert msg in {x.decode() for x in rds.smembers('insults')}
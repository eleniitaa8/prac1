import pytest, redis, multiprocessing, time
from redis_impl.insult_filter.worker import worker

@pytest.fixture(scope='module')
def rds():
    r = redis.Redis()
    r.flushdb()
    r.sadd('insults', 'badword')
    return r

@pytest.fixture(scope='module', autouse=True)
def start_worker(rds):
    # arrancamos el worker en un proceso real
    p = multiprocessing.Process(target=worker)
    p.start()
    # le damos un poco más de tiempo a Windows para levantar el proceso y llegar al BLPOP
    time.sleep(0.5)
    yield
    p.terminate()
    p.join()

def test_filtering(rds):
    # encolamos la tarea
    rds.rpush('filter_tasks', 'hello badword world')

    # polling activo durante hasta 2 segundos
    deadline = time.time() + 2.0
    results = []
    while time.time() < deadline:
        results = [x.decode('utf-8') for x in rds.lrange('filter_results', 0, -1)]
        if 'hello CENSORED world' in results:
            break
        time.sleep(0.1)

    assert 'hello CENSORED world' in results

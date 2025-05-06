import pytest, Pyro4, multiprocessing, time, os, sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root)
from pyro4_impl.insult_service import service as svc_mod

@pytest.fixture(scope='module', autouse=True)
def start_srv():
    p = multiprocessing.Process(target=svc_mod.main)
    p.start(); time.sleep(1)
    yield

def test_add_and_list():
    proxy = Pyro4.Proxy("PYRO:InsultService@localhost:9000")
    assert proxy.add_insult('foo') is True
    assert proxy.add_insult('foo') is False
    assert 'foo' in proxy.get_insults()

def test_subscribe():
    proxy = Pyro4.Proxy("PYRO:InsultService@localhost:9000")
    assert proxy.subscribe('PYRO:Dummy@localhost:1234') is True
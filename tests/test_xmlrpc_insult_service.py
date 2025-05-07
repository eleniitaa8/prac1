# tests/test_xmlrpc_insult_service.py
import pytest, xmlrpc.client, multiprocessing, time, os, sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root)
import xmlrpc_impl.insult_service.service as svc_mod

@pytest.fixture(scope='module', autouse=True)
def start_srv():
    p = multiprocessing.Process(target=svc_mod.main)
    p.start()
    time.sleep(1)
    yield
    p.terminate()


def test_add_list():
    proxy = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
    assert proxy.add_insult('foo')
    assert not proxy.add_insult('foo')
    assert 'foo' in proxy.get_insults()


def test_subscribe():
    proxy = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
    assert proxy.subscribe('localhost', 9001)
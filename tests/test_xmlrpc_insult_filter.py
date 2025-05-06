# tests/test_xmlrpc_insult_filter.py
import pytest, xmlrpc.client, multiprocessing, time, os, sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root)
from xmlrpc_impl.insult_service import service as svc_mod
from xmlrpc_impl.insult_filter import service as filt_mod

@pytest.fixture(scope='module', autouse=True)
def start_both():
    p1 = multiprocessing.Process(target=svc_mod.main)
    p1.start(); time.sleep(1)
    p2 = multiprocessing.Process(target=filt_mod.main)
    p2.start(); time.sleep(1)
    yield

def test_filtering():
    svc = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
    filt = xmlrpc.client.ServerProxy('http://localhost:8010', allow_none=True)
    svc.add_insult('badword'); time.sleep(0.1)
    assert filt.add_text('hey badword')
    res = filt.get_results()
    assert res and 'CENSORED' in res[0]

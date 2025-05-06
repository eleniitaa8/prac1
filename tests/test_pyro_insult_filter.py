import pytest, Pyro4, multiprocessing, time, os, sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root)
from pyro4_impl.insult_service import service as svc_mod
from pyro4_impl.insult_filter import service as filt_mod

@pytest.fixture(scope='module', autouse=True)
def start_both():
    p1 = multiprocessing.Process(target=svc_mod.main)
    p1.start(); time.sleep(1)
    p2 = multiprocessing.Process(target=filt_mod.main)
    p2.start(); time.sleep(1)
    yield

def test_filtering():
    svc = Pyro4.Proxy("PYRO:InsultService@localhost:9000")
    filt = Pyro4.Proxy("PYRO:InsultFilterService@localhost:9015")
    svc.add_insult('badword'); time.sleep(0.1)
    assert filt.add_text('hey badword') is True
    res = filt.get_results()
    assert res and 'CENSORED' in res[0]
# tests/test_xmlrpc_broadcaster.py
import pytest, threading, time, xmlrpc.client, os, sys
from xmlrpc.server import SimpleXMLRPCServer
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root)
import xmlrpc_impl.insult_service.service as svc_mod

pytestmark = pytest.mark.filterwarnings(
    "ignore:.*isSet\\(\\) is deprecated.*:DeprecationWarning"
)

@pytest.fixture(scope='module', autouse=True)
def start_service():
    from multiprocessing import Process
    p = Process(target=svc_mod.main)
    p.start(); time.sleep(1)
    yield
    p.terminate()


def test_broadcaster_push():
    received = []
    class StubHandler:
        def receive_insult(self, insult):
            received.append(insult)
            return True
    port = 9001
    stub = SimpleXMLRPCServer(('0.0.0.0', port), allow_none=True)
    stub.register_instance(StubHandler())
    stub_thread = threading.Thread(target=stub.serve_forever, daemon=True)
    stub_thread.start(); time.sleep(1)
    proxy = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
    assert proxy.subscribe('localhost', port)
    proxy.add_insult('hello')
    time.sleep(6)
    assert 'hello' in received
    stub.shutdown()
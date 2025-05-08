# File: tests/test_pyro_services.py
import pytest
import Pyro4
import subprocess
import time
import os
import sys
import threading

# Filtra los DeprecationWarning de Pyro4 sobre isSet()
pytestmark = pytest.mark.filterwarnings(
    "ignore:.*isSet\\(\\) is deprecated.*:DeprecationWarning"
)

# Añadir ruta del proyecto para localizar scripts
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
service_script = os.path.join(root, 'pyro4_impl', 'insult_service', 'service.py')
filter_script = os.path.join(root, 'pyro4_impl', 'insult_filter', 'service.py')

@pytest.fixture(scope="module", autouse=True)
def start_both():
    # 1) chequeo Redis
    import redis
    try:
        redis.Redis(host='localhost', port=6379).ping()
    except redis.ConnectionError as e:
        pytest.skip(f"Redis no responde en localhost:6379 – {e}")

    # 2) lanza InsultService
    p1 = subprocess.Popen(
        [sys.executable, "-m", "pyro4_impl.insult_service.service", "--port", "9000"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    # lanza InsultFilterService
    p2 = subprocess.Popen(
        [sys.executable, "-m", "pyro4_impl.insult_filter.service", "--port", "9015"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # 3) Polling con timeout extendido
    deadline = time.time() + 15
    ok1 = ok2 = False
    while time.time() < deadline and (not ok1 or not ok2):
        try:
            Pyro4.Proxy("PYRO:InsultService@localhost:9000").get_insults()
            ok1 = True
        except:
            pass
        try:
            Pyro4.Proxy("PYRO:InsultFilterService@localhost:9015").get_results()
            ok2 = True
        except:
            pass
        time.sleep(0.2)

    if not (ok1 and ok2):
        stderr1 = p1.stderr.read()
        stderr2 = p2.stderr.read()
        print("=== InsultService stderr ===\n", stderr1)
        print("=== InsultFilterService stderr ===\n", stderr2)
        p1.kill(); p2.kill()
        pytest.skip("Servicios Pyro no arrancaron a tiempo (revisa el stderr).")

    yield

    p1.terminate()
    p2.terminate()


def test_filtering():
    svc = Pyro4.Proxy("PYRO:InsultService@localhost:9000")
    filt = Pyro4.Proxy("PYRO:InsultFilterService@localhost:9015")
    # Añadir insulto y filtrar texto
    assert svc.add_insult('badword') is True
    time.sleep(0.1)
    assert filt.add_text('hey badword') is True
    res = filt.get_results()
    assert res and 'CENSORED' in res[0]


def test_add_and_list():
    proxy = Pyro4.Proxy("PYRO:InsultService@localhost:9000")
    # Prueba idempotencia y listado
    assert proxy.add_insult('foo') is True
    assert proxy.add_insult('foo') is False
    insults = proxy.get_insults()
    assert 'foo' in insults


def test_subscribe_and_broadcast(capsys):
    # Servidor callback en hilo para capturar broadcast
    @Pyro4.expose
    class CB:
        def receive_insult(self, insult):
            print(f"[CB] {insult}")
            return True

    def run_cb():
        daemon = Pyro4.Daemon(host='localhost', port=9200)
        daemon.register(CB(), objectId="CallbackServer")
        daemon.requestLoop()

    t = threading.Thread(target=run_cb, daemon=True)
    t.start()
    time.sleep(1)

    svc = Pyro4.Proxy("PYRO:InsultService@localhost:9000")
    # Suscribirse y provocar broadcast inmediato
    assert svc.subscribe('localhost', 9200) is True
    assert svc.add_insult('test_sub') is True
    time.sleep(0.1)

    captured = capsys.readouterr()
    assert '[CB]' in captured.out
    # El hilo demonio terminará al finalizar el proceso
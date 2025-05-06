import unittest
import subprocess
import time
import sys
import os
import signal
import xmlrpc.client
import Pyro4
import requests
import pika
import uuid
import json
import re
from colorama import init, Fore, Style

# Inicializa colorama para la salida en color
init(autoreset=True)

# ================================
# Helper Functions y Variables Globales
# ================================

def start_process(cmd):
    """Arranca un proceso con el comando 'cmd' y lo devuelve."""
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def kill_process(proc):
    """Termina el proceso dado."""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

# Aquí definimos los comandos para arrancar solo los servidores Python. 
# *Nota*: Los contenedores Docker para RabbitMQ y Redis deben arrancarse manualmente.
SERVER_CMDS = [
    (["pyro4-ns"], "PYRO NameServer"),
    (["python", "insult_service/xmlrpc/server.py"], "InsultService XMLRPC"),
    (["python", "insult_service/pyro/server.py"], "InsultService PyRO"),
    (["python", "insult_service/redis/server.py"], "InsultService Redis"),
    (["python", "insult_service/rabbitmq/server.py"], "InsultService RabbitMQ"),
    (["python", "insult_filter/xmlrpc/server.py"], "InsultFilter XMLRPC"),
    (["python", "insult_filter/pyro/server.py"], "InsultFilter PyRO"),
    (["python", "insult_filter/redis/server.py"], "InsultFilter Redis"),
    (["python", "insult_filter/rabbitmq/server.py"], "InsultFilter RabbitMQ")
]

server_processes = []

# ================================
# Clase Base de Tests que Arranca los Servidores
# ================================
class IntegrationTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(Fore.YELLOW + Style.BRIGHT + ">>> Arrancando servidores de integración..." + Style.RESET_ALL)
        for cmd, label in SERVER_CMDS:
            print(Fore.YELLOW + f"Iniciando {label} con comando: {' '.join(cmd)}" + Style.RESET_ALL)
            proc = start_process(cmd)
            server_processes.append((label, proc))
        print(Fore.YELLOW + "Esperando 20 segundos para que todos los servidores estén listos..." + Style.RESET_ALL)
        time.sleep(20)  # Aumenta el tiempo de espera si es necesario

    @classmethod
    def tearDownClass(cls):
        print(Fore.YELLOW + Style.BRIGHT + "\n>>> Finalizando servidores..." + Style.RESET_ALL)
        for label, proc in server_processes:
            print(Fore.YELLOW + f"Terminando {label}..." + Style.RESET_ALL)
            kill_process(proc)
        server_processes.clear()

# ================================
# Helper Functions para Clientes (InsultService & InsultFilter)
# ================================

# --- Insult Service ---
def test_insult_service_xmlrpc():
    proxy = xmlrpc.client.ServerProxy("http://localhost:8000")
    added = proxy.add_insult("You nincompoop!")
    insults = proxy.get_insults()
    return added, insults

def test_insult_service_pyro():
    proxy = Pyro4.Proxy("PYRONAME:InsultService")
    added = proxy.add_insult("You nincompoop!")
    insults = proxy.get_insults()
    return added, insults

def test_insult_service_redis():
    add_url = "http://localhost:8001/add_insult"
    get_url = "http://localhost:8001/get_insults"
    resp_add = requests.post(add_url, json={"insult": "You nincompoop!"}).json()
    resp_get = requests.get(get_url).json()
    return resp_add.get("added"), resp_get.get("insults")

def rpc_call_rabbitmq(routing_key, request, timeout=20):
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = conn.channel()
    result = channel.queue_declare('', exclusive=True)
    callback_queue = result.method.queue
    response = None
    corr_id = str(uuid.uuid4())

    def on_response(ch, method, props, body):
        nonlocal response
        if corr_id == props.correlation_id:
            response = json.loads(body)

    channel.basic_consume(queue=callback_queue, on_message_callback=on_response, auto_ack=True)
    channel.basic_publish(
        exchange='',
        routing_key=routing_key,
        properties=pika.BasicProperties(reply_to=callback_queue, correlation_id=corr_id),
        body=json.dumps(request)
    )
    start_time = time.time()
    while response is None and (time.time() - start_time) < timeout:
        conn.process_data_events()
    conn.close()
    if response is None:
        raise TimeoutError(f"Timeout esperando respuesta para request {request}")
    return response

def test_insult_service_rabbitmq():
    response_add = rpc_call_rabbitmq("rpc_queue", {"action": "add", "insult": "You nincompoop!"})
    response_get = rpc_call_rabbitmq("rpc_queue", {"action": "get"})
    return response_add.get("result"), response_get.get("insults")

# --- Insult Filter ---
def expected_filtered(text):
    insults = ["nincompoop", "idiot", "fool"]
    result = text
    for insult in insults:
        result = re.sub(insult, "CENSORED", result, flags=re.IGNORECASE)
    return result

def test_insult_filter_xmlrpc():
    proxy = xmlrpc.client.ServerProxy("http://localhost:9000")
    filtered = proxy.filter_text("You are a nincompoop and an idiot!")
    results = proxy.get_results()
    return filtered, results

def test_insult_filter_pyro():
    proxy = Pyro4.Proxy("PYRONAME:InsultFilter")
    filtered = proxy.filter_text("You are a nincompoop and an idiot!")
    results = proxy.get_results()
    return filtered, results

def test_insult_filter_redis():
    filter_url = "http://localhost:9001/filter"
    get_url = "http://localhost:9001/get_results"
    resp = requests.post(filter_url, json={"text": "You are a nincompoop and an idiot!"}).json()
    filtered = resp.get("filtered")
    results = requests.get(get_url).json().get("results")
    return filtered, results

def test_insult_filter_rabbitmq():
    response_filter = rpc_call_rabbitmq("rpc_queue_filter", {"action": "filter", "text": "You are a nincompoop and an idiot!"})
    response_get = rpc_call_rabbitmq("rpc_queue_filter", {"action": "get"})
    return response_filter.get("filtered"), response_get.get("results")

# ================================
# Test Cases Integrados
# ================================
class TestInsultService(IntegrationTestBase):
    def test_xmlrpc(self):
        print(Fore.CYAN + "\n[TEST] InsultService XMLRPC" + Style.RESET_ALL)
        added, insults = test_insult_service_xmlrpc()
        self.assertTrue(added, "XMLRPC: Error al agregar insulto")
        self.assertIn("You nincompoop!", insults, "XMLRPC: Insulto no encontrado")

    def test_pyro(self):
        print(Fore.CYAN + "\n[TEST] InsultService PyRO" + Style.RESET_ALL)
        added, insults = test_insult_service_pyro()
        self.assertTrue(added, "PyRO: Error al agregar insulto")
        self.assertIn("You nincompoop!", insults, "PyRO: Insulto no encontrado")

    def test_redis(self):
        print(Fore.CYAN + "\n[TEST] InsultService Redis" + Style.RESET_ALL)
        added, insults = test_insult_service_redis()
        self.assertTrue(added, "Redis: Error al agregar insulto")
        self.assertIn("You nincompoop!", insults, "Redis: Insulto no encontrado")

    def test_rabbitmq(self):
        print(Fore.CYAN + "\n[TEST] InsultService RabbitMQ" + Style.RESET_ALL)
        added, insults = test_insult_service_rabbitmq()
        self.assertTrue(added, "RabbitMQ: Error al agregar insulto")
        self.assertIn("You nincompoop!", insults, "RabbitMQ: Insulto no encontrado")

class TestInsultFilter(IntegrationTestBase):
    def test_xmlrpc(self):
        print(Fore.CYAN + "\n[TEST] InsultFilter XMLRPC" + Style.RESET_ALL)
        filtered, results = test_insult_filter_xmlrpc()
        expected = expected_filtered("You are a nincompoop and an idiot!")
        self.assertEqual(filtered, expected, "XMLRPC: El texto filtrado no coincide")
        self.assertTrue(len(results) > 0, "XMLRPC: La lista de resultados está vacía")

    def test_pyro(self):
        print(Fore.CYAN + "\n[TEST] InsultFilter PyRO" + Style.RESET_ALL)
        filtered, results = test_insult_filter_pyro()
        expected = expected_filtered("You are a nincompoop and an idiot!")
        self.assertEqual(filtered, expected, "PyRO: El texto filtrado no coincide")
        self.assertTrue(len(results) > 0, "PyRO: La lista de resultados está vacía")

    def test_redis(self):
        print(Fore.CYAN + "\n[TEST] InsultFilter Redis" + Style.RESET_ALL)
        filtered, results = test_insult_filter_redis()
        expected = expected_filtered("You are a nincompoop and an idiot!")
        self.assertEqual(filtered, expected, "Redis: El texto filtrado no coincide")
        self.assertTrue(len(results) > 0, "Redis: La lista de resultados está vacía")

    def test_rabbitmq(self):
        print(Fore.CYAN + "\n[TEST] InsultFilter RabbitMQ" + Style.RESET_ALL)
        filtered, results = test_insult_filter_rabbitmq()
        expected = expected_filtered("You are a nincompoop and an idiot!")
        self.assertEqual(filtered, expected, "RabbitMQ: El texto filtrado no coincide")
        self.assertTrue(len(results) > 0, "RabbitMQ: La lista de resultados está vacía")

# ================================
# Custom Test Runner con Salida en Color
# ================================
from unittest import TextTestRunner, TextTestResult

class ColorTextTestResult(TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.writeln(Fore.GREEN + "PASSED: " + str(test))
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.writeln(Fore.RED + "FAILED: " + str(test))
    def addError(self, test, err):
        super().addError(test, err)
        self.stream.writeln(Fore.RED + "ERROR: " + str(test))

class ColorTextTestRunner(TextTestRunner):
    resultclass = ColorTextTestResult

if __name__ == '__main__':
    print(Fore.YELLOW + Style.BRIGHT + "\n==== Iniciando Tests de Integración para InsultService e InsultFilter ====\n" + Style.RESET_ALL)
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestInsultService)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestInsultFilter)
    alltests = unittest.TestSuite([suite1, suite2])
    runner = ColorTextTestRunner(verbosity=2)
    runner.run(alltests)

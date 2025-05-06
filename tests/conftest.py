# tests/conftest.py
import socket
import time
import pytest
import pika

@pytest.fixture(scope='session', autouse=True)
def wait_for_services():
    # 1) Esperar Redis (puerto 6379)
    deadline = time.time() + 15.0
    while time.time() < deadline:
        try:
            s = socket.create_connection(('127.0.0.1', 6379), timeout=1)
            s.close()
            break
        except OSError:
            time.sleep(0.3)
    else:
        pytest.exit("Redis no respondió en 6379 en 15s")

    # 2) Esperar RabbitMQ (AMQP handshake en 5672)
    deadline = time.time() + 30.0
    while time.time() < deadline:
        try:
            conn = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1', 5672))
            conn.close()
            break  # ¡listo!
        except Exception:
            time.sleep(0.5)
    else:
        pytest.exit("RabbitMQ no respondió al handshake AMQP en 5672 en 30s")

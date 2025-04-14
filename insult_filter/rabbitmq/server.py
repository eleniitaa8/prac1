import pika
import json
import re
import uuid
import threading
import time

INSULTS = ["nincompoop", "idiot", "fool"]
results = []  # Lista para almacenar los textos filtrados

def filter_text(text):
    filtered = text
    for insult in INSULTS:
        filtered = re.sub(insult, "CENSORED", filtered, flags=re.IGNORECASE)
    results.append(filtered)
    return filtered

def on_request(ch, method, properties, body):
    request = json.loads(body)
    if request["action"] == "filter":
        text = request.get("text", "")
        filtered = filter_text(text)
        response = {"filtered": filtered}
    elif request["action"] == "get":
        response = {"results": results}
    else:
        response = {"error": "Unknown action"}
    
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(correlation_id=properties.correlation_id),
        body=json.dumps(response)
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Configuración de conexión y cola RPC para InsultFilter.
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='rpc_queue_filter')
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue_filter', on_message_callback=on_request)

print("RabbitMQ InsultFilter RPC server running")
channel.start_consuming()

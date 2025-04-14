import pika
import json
import threading
import time
import random

# In-memory storage for insults.
insults = set()

# Establish connection to RabbitMQ.
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare the broadcast exchange.
channel.exchange_declare(exchange='insult_broadcast', exchange_type='fanout')

def on_request(ch, method, properties, body):
    request = json.loads(body)
    if request["action"] == "add":
        insult = request["insult"]
        if insult not in insults:
            insults.add(insult)
            response = {"result": True}
        else:
            response = {"result": False}
    elif request["action"] == "get":
        response = {"insults": list(insults)}
    
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(correlation_id=properties.correlation_id),
        body=json.dumps(response)
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Set up RPC queue.
channel.queue_declare(queue='rpc_queue')
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

def broadcast_insults():
    while True:
        if insults:
            insult = random.choice(list(insults))
            channel.basic_publish(exchange='insult_broadcast', routing_key='', body=insult)
            print("Broadcasted:", insult)
        time.sleep(5)

# Start the broadcaster thread.
threading.Thread(target=broadcast_insults, daemon=True).start()
print("RabbitMQ InsultService RPC server running")
channel.start_consuming()

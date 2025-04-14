import pika
import uuid
import json

class RpcClient:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()

        result = self.channel.queue_declare('', exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue, on_message_callback=self.on_response, auto_ack=True
        )
        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = json.loads(body)

    def call(self, request):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue, correlation_id=self.corr_id
            ),
            body=json.dumps(request)
        )
        while self.response is None:
            self.connection.process_data_events()
        return self.response

if __name__ == "__main__":
    rpc = RpcClient()
    # Add insult via RPC.
    response = rpc.call({"action": "add", "insult": "Caca"})
    print("Add insult response:", response)
    # Retrieve list of insults.
    response = rpc.call({"action": "get"})
    print("Stored insults:", response)

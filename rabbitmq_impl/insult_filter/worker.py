import pika, json
import uuid

class InsultRpcClient:
    """Reutilizamos el cliente RPC del servicio de insultos."""
    def __init__(self):
        self.conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.ch = self.conn.channel()
        res = self.ch.queue_declare('', exclusive=True)
        self.callback_queue = res.method.queue
        self.ch.basic_consume(queue=self.callback_queue,
                              on_message_callback=self.on_response,
                              auto_ack=True)
        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if props.correlation_id == self.corr_id:
            self.response = json.loads(body)

    def call(self, method):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        payload = {'method': method}
        self.ch.basic_publish(
            exchange='',
            routing_key='insult_rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id
            ),
            body=json.dumps(payload)
        )
        while self.response is None:
            self.conn.process_data_events()
        return self.response

def worker():
    import uuid
    rpc = InsultRpcClient()
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    ch.queue_declare(queue='filter_queue')
    ch.queue_declare(queue='filter_results_queue')

    def on_request(ch, method, props, body):
        text = body.decode('utf-8')
        # obtengo insultos remotos
        insults = rpc.call('get_insults')['insults']
        filtered = text
        for ins in insults:
            filtered = filtered.replace(ins, 'CENSORED')
        ch.basic_publish(
            exchange='',
            routing_key='filter_results_queue',
            body=filtered
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue='filter_queue', on_message_callback=on_request)
    print("[FilterWorker] escuchando en 'filter_queue'")
    ch.start_consuming()

if __name__ == '__main__':
    worker()

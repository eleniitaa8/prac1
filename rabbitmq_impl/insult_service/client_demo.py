import pika, json, uuid, time

class InsultRpcClient:
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

    def call(self, method, text=None):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        payload = {'method': method}
        if text is not None:
            payload['text'] = text
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

if __name__ == '__main__':
    client = InsultRpcClient()

    # 1) Añadir insultos
    for insult in ('idiot','dummy','fool'):
        res = client.call('add_insult', insult)
        print(f"Add '{insult}':", res['success'])
        #print(f"Add '{insult}':", res['success'])

    # 2) Obtener listado
    res = client.call('get_insults')
    print("Current insults:", res['insults'])

    # 3) Suscribirse a broadcasts
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    ch.exchange_declare(exchange='insults_exchange', exchange_type='fanout')
    q = ch.queue_declare('', exclusive=True).method.queue
    ch.queue_bind(exchange='insults_exchange', queue=q)
    print("[Callback] suscrito a 'insults_exchange', esperando mensajes")
    for method, props, body in ch.consume(q, auto_ack=True):
        print("[Broadcast]", body.decode())

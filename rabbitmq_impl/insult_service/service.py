# rabbitmq_impl/insult_service/service.py
import pika
import json
import time
import random
import argparse
import multiprocessing

def rpc_server(insults, lock):
    # Conexión y cola para RPC
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    ch.queue_declare(queue='insult_rpc_queue')

    def on_request(ch, method, props, body):
        try:
            req = json.loads(body)
        except Exception:
            resp = {'error': 'invalid JSON'}
        else:
            m = req.get('method')
            if m == 'add_insult':
                text = req.get('text')
                if text is None:
                    success = False
                else:
                    with lock:
                        if text not in insults:
                            insults.append(text)
                            success = True
                        else:
                            success = False
                resp = {'success': success}

            elif m == 'get_insults':
                with lock:
                    resp = {'insults': list(insults)}
            else:
                resp = {'error': 'unknown method'}

        # respond
        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=json.dumps(resp)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue='insult_rpc_queue', on_message_callback=on_request)
    ch.start_consuming()

def broadcaster(insults, lock, interval):
    # Publica insultos en fanout cada `interval`
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    ch.exchange_declare(exchange='insults_exchange', exchange_type='fanout')
    while True:
        time.sleep(interval)
        with lock:
            if not insults:
                continue
            insult = random.choice(insults)
        ch.basic_publish(exchange='insults_exchange', routing_key='', body=insult)

def main():
    # parse_known_args ignora flags extra (ej. los de pytest)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--interval', type=float, default=1.0,
                        help='segundos entre broadcasts')
    args, _ = parser.parse_known_args()

    mgr = multiprocessing.Manager()
    insults = mgr.list()
    lock = multiprocessing.Lock()

    # arrancamos broadcaster con interval
    p = multiprocessing.Process(target=broadcaster,
                                args=(insults, lock, args.interval),
                                daemon=True)
    p.start()

    print(f"[InsultService] RPC + broadcaster arrancados "
          f"(interval={args.interval}s)")
    rpc_server(insults, lock)

if __name__ == '__main__':
    main()

import pika, time

if __name__ == '__main__':
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    ch.queue_declare(queue='filter_queue')
    ch.queue_declare(queue='filter_results_queue')

    texts = ['You are an idiot','Hello world','You dummy again']
    for t in texts:
        ch.basic_publish(exchange='', routing_key='filter_queue', body=t)
        print("Submitted:", t)

    time.sleep(0.5)
    print("Results:")
    while True:
        method, props, body = ch.basic_get('filter_results_queue', auto_ack=True)
        if not body:
            break
        print("  ", body.decode())

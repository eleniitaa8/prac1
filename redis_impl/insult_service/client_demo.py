import time
import redis

if __name__ == '__main__':
    rds = redis.Redis()

    # 1) Añadir insultos
    for insult in ('idiot', 'dummy', 'fool'):
        added = rds.sadd('insults', insult)
        print(f"Add '{insult}': {bool(added)}")

    # 2) Listar insultos
    current = {x.decode() for x in rds.smembers('insults')}
    print("Current insults:", current)

    # 3) Suscribirse a canal
    pubsub = rds.pubsub()
    pubsub.subscribe('insults_channel')
    print("[Callback] suscrito, esperando broadcasts...")

    # 4) Recibir mensajes
    try:
        for msg in pubsub.listen():
            if msg['type'] == 'message':
                print(f"[Broadcast] {msg['data'].decode()}")
    except KeyboardInterrupt:
        print("Demo cliente finalizado.")
import time, random
import redis

def broadcaster(interval: float = 5.0):
    """
    Cada 'interval' segundos, publica un insulto aleatorio
    desde el set 'insults' al canal 'insults_channel'.
    """
    rds = redis.Redis()
    channel = 'insults_channel'
    while True:
        time.sleep(interval)
        insults = rds.smembers('insults')
        if not insults:
            continue
        # seleccionar y publicar insulto
        insult = random.choice(list(insults)).decode('utf-8')
        rds.publish(channel, insult)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=float, default=5.0,
                        help='segundos entre broadcasts')
    args = parser.parse_args()
    print(f"[InsultService] Broadcaster corriendo cada {args.interval}s...")
    broadcaster(args.interval)

if __name__ == '__main__':
    main()
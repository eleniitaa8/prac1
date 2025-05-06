import time
import redis

if __name__ == '__main__':
    rds = redis.Redis()
    texts = [
        'You are an idiot',
        'Hello world',
        'You dummy again'
    ]
    for t in texts:
        rds.rpush('filter_tasks', t)
        print("Submitted:", t)

    time.sleep(0.1)
    results = [x.decode('utf-8') for x in rds.lrange('filter_results', 0, -1)]
    print("Filtered:", results)
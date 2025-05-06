# redis_impl/insult_filter/worker.py
import redis

def worker():
    rds = redis.Redis()
    # bloqueamos indefinidamente hasta que haya algo en filter_tasks
    while True:
        # timeout=0 → BLPOP bloquea hasta que encuentre un elemento
        task = rds.blpop('filter_tasks', timeout=0)
        # si devolviera None (muy improbable con timeout=0), seguimos
        if not task:
            continue
        _, raw = task
        text = raw.decode('utf-8')

        insults = {x.decode('utf-8') for x in rds.smembers('insults')}
        filtered = text
        for ins in insults:
            filtered = filtered.replace(ins, 'CENSORED')

        rds.rpush('filter_results', filtered)

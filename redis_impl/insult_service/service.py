# service.py
import redis
import json

class InsultService:
    def __init__(self, redis_host='localhost', redis_port=6379, max_connections=None):
        # Crear un pool de conexiones si se especifica
        if max_connections:
            pool = redis.ConnectionPool(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                max_connections=max_connections
            )
            self.r = redis.Redis(connection_pool=pool)
        else:
            self.r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

        self.insults_key = 'insults'
        self.channel = 'insults_channel'

    def start(self):
        print("[InsultService] Listening for requests on 'insult_requests'...")
        while True:
            _, message = self.r.blpop('insult_requests')
            req = json.loads(message)
            command = req.get('command')
            client_id = req.get('client_id')
            response_stream = f"insult_responses:{client_id}"
            if command == 'add_insult':
                insult = req.get('insult')
                added = self.r.sadd(self.insults_key, insult)
                if added:
                    self.r.publish(self.channel, insult)
                resp = {'added': bool(added)}
                self.r.rpush(response_stream, json.dumps(resp))
            elif command == 'get_insults':
                insults = list(self.r.smembers(self.insults_key))
                resp = {'insults': insults}
                self.r.rpush(response_stream, json.dumps(resp))
            else:
                resp = {'error': f"Unknown command {command}"}
                self.r.rpush(response_stream, json.dumps(resp))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis-host', default='localhost')
    parser.add_argument('--redis-port', type=int, default=6379)
    parser.add_argument('--max-connections', type=int, default=None,
                        help='Máximo número de conexiones en el pool')
    args = parser.parse_args()
    service = InsultService(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        max_connections=args.max_connections
    )
    service.start()
import time
from redis.exceptions import TimeoutError

from utils import echo


def on_timeout(f):
    def wrapper(*args, **kwargs):
        for _ in range(100):
            try:
                return f(*args, **kwargs)
            except TimeoutError as e:
                args[0].attempts.append(e)
                echo('Timeout error reading from socket. '
                     'Trying again in 10 seconds.',
                     color='red')
                time.sleep(10)
        raise

    return wrapper

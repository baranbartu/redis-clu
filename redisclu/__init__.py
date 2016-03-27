from redis import connection
from redis.exceptions import (ResponseError)
from exceptions import (AskError, MovedError)

import logging

logging.basicConfig()

CUSTOM_EXCEPTION_CLASSES = {
    'ASK': AskError,
    'MOVED': MovedError,
}


def parse_error(self, response):
    "Parse an error response"
    error_code = response.split(' ')[0]
    if error_code in self.EXCEPTION_CLASSES:
        response = response[len(error_code) + 1:]
        exception_class = self.EXCEPTION_CLASSES[error_code]
        if isinstance(exception_class, dict):
            for reason, inner_exception_class in exception_class.items():
                if reason in response:
                    return inner_exception_class(response)
            return ResponseError(response)
        return exception_class(response)
    return ResponseError(response)


connection.BaseParser.EXCEPTION_CLASSES.update(CUSTOM_EXCEPTION_CLASSES)
connection.BaseParser.parse_error = parse_error

from redis.exceptions import (
    ResponseError
)


class RedisCluException(Exception):
    pass


class AskError(ResponseError):
    """
    partially keys is slot migrated to another node

    src node: MIGRATING to dst node
        get > ASK error
        ask dst node > ASKING command
    dst node: IMPORTING from src node
        asking command only affects next command
        any op will be allowed after asking command
    """

    def __init__(self, resp):
        """should only redirect to master node"""
        self.args = (resp,)
        self.message = resp
        slot_id, new_node = resp.split(' ')
        host, port = new_node.rsplit(':', 1)
        self.slot_id = int(slot_id)
        self.node_addr = self.host, self.port = host, int(port)


class MovedError(AskError):
    """
    all keys in slot migrated to another node
    """
    pass


class ClusterNotHealthy(RedisCluException):
    pass


class ClusterNotConsistent(RedisCluException):
    pass
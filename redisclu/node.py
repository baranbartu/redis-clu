import socket
import redis
import urlparse

from exceptions import (AskError, MovedError)
from utils import echo


class Node(object):
    ignored_exceptions = (AskError, MovedError)

    def __init__(self, host='localhost', port=6379, socket_timeout=4):
        self.host = socket.gethostbyname(host)
        self.port = port
        self.redis = redis.Redis(host, port, socket_timeout=socket_timeout)
        self.redis.ping()
        self.pipeline = self.redis.pipeline(transaction=False)
        self.attempts = []

    @classmethod
    def from_uri(cls, uri):
        if not uri.startswith('redis://'):
            uri = 'redis://{}'.format(uri)
        d = urlparse.urlparse(uri)
        return cls(d.hostname, d.port)

    def __repr__(self):
        return 'Node<{}:{}>'.format(self.host, self.port)

    def __getattr__(self, attr):
        return getattr(self.redis, attr)

    def execute_command(self, *args, **kwargs):
        return self.redis.execute_command(*args, **kwargs)

    def is_slave(self, master_id=None):
        info = self.node_info

        r = 'slave' in info['flags']
        if master_id is not None:
            r = r and info['replicate'] == master_id
        return r

    def is_master(self):
        return 'master' in self.node_info['flags']

    @property
    def node_info(self):
        nodes = self.nodes()
        return nodes[0]

    @property
    def slots(self):
        return self.node_info['slots']

    @property
    def name(self):
        return self.node_info['name']

    def migrate_keys(self, host, port, keys):
        for key in keys:
            self.pipeline.execute_command('MIGRATE', host, port, key, 0, 15000)
        return self.pipeline.execute(raise_on_error=False)

    def migrate_slot(self, dst, slot, cluster):
        dst.set_slot('IMPORTING', slot, self.name)
        self.set_slot('MIGRATING', slot, dst.name)

        total_keys = 0
        for keys in self._scan_keys(slot, cluster.key_migration_count):
            results = self.migrate_keys(dst.host, dst.port, keys)
            self.attempts.extend(filter(lambda r: any(
                isinstance(r, e) for e in self.ignored_exceptions), results))
            total_keys += len(keys)

        echo('{} key(s) migrated from {} to {} in slot {}'.format(
            total_keys, self, dst, slot))

        cluster.update_slot_mapping(slot, dst.name)

    def reset(self, hard=False):
        args = []
        if hard:
            args = ['HARD']
        return self.execute_command('CLUSTER RESET', *args)

    def set_slot(self, action, slot, node_id=None):
        remain = [node_id] if node_id else []
        return self.execute_command('CLUSTER SETSLOT', slot, action, *remain)

    def get_keys_in_slot(self, slot, count):
        return self.execute_command('CLUSTER GETKEYSINSLOT', slot, count)

    def count_keys_in_slot(self, slot):
        return self.execute_command('CLUSTER COUNTKEYSINSLOT', slot)

    def slaves(self, node_id):
        data = self.execute_command('CLUSTER SLAVES', node_id)
        return self._parse_node('\n'.join(data))

    def add_slots(self, *slot):
        if not slot:
            return
        self.execute_command('CLUSTER ADDSLOTS', *slot)

    def forget(self, node_id):
        return self.execute_command('CLUSTER FORGET', node_id)

    def set_config_epoch(self, config_epoch):
        return self.execute_command('CLUSTER SET-CONFIG-EPOCH', config_epoch)

    def meet(self, ip, port):
        return self.execute_command('CLUSTER MEET', ip, port)

    def replicate(self, node_id):
        return self.execute_command('CLUSTER REPLICATE', node_id)

    def nodes(self):
        info = self.execute_command('CLUSTER NODES').strip()
        return self._parse_node(info)

    def cluster_info(self):
        data = {}
        info = self.execute_command('CLUSTER INFO').strip()
        for item in info.split('\r\n'):
            k, v = item.split(':')
            if k != 'cluster_state':
                v = int(v)
            data[k] = v
        return data

    def _parse_node(self, nodes):
        data = []
        for item in nodes.split('\n'):
            if not item:
                continue
            confs = item.split()
            node_info = {
                'name': confs[0],
                'addr': confs[1],
                'flags': confs[2].split(','),
                'replicate': confs[3],  # master_id
                'ping_sent': int(confs[4]),
                'ping_recv': int(confs[5]),
                'link_status': confs[7],
                'migrating': {},
                'importing': {},
                'slots': []
            }
            for slot in confs[8:]:
                if slot[0] == '[':
                    if '->-' in slot:
                        s, dst = slot[1:-1].split('->-')
                        node_info['migrating'][s] = dst
                    elif '-<-' in slot:
                        s, src = slot[1:-1].split('-<-')
                        node_info['importing'][s] = src
                elif '-' in slot:
                    start, end = slot.split('-')
                    node_info['slots'].extend(range(int(start), int(end) + 1))
                else:
                    node_info['slots'].append(int(slot))

            if 'myself' in node_info['flags']:
                data.insert(0, node_info)
            else:
                data.append(node_info)
        return data

    def _scan_keys(self, slot, count):
        while True:
            keys = self.get_keys_in_slot(slot, count)
            if not keys:
                break
            yield keys

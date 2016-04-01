import time
import itertools
import hashlib
import failover

from node import Node
from exceptions import (ClusterNotHealthy, ClusterNotConsistent)
from utils import (divide, echo)


class Cluster(object):
    CLUSTER_HASH_SLOTS = 16384

    def __init__(self, nodes, hash_slots=CLUSTER_HASH_SLOTS,
                 parent_nodes=None):
        self.nodes = nodes
        self.parent_nodes = parent_nodes if parent_nodes else nodes
        self.CLUSTER_HASH_SLOTS = hash_slots
        self.attempts = []
        self.key_migration_count = 1

    @classmethod
    def from_node(cls, node):
        nodes = [Node.from_uri(i['addr']) for i in node.nodes()
                 if i['link_status'] != 'disconnected']
        return cls(nodes)

    @property
    def masters(self):
        return [i for i in self.nodes if i.is_master()]

    def set_key_migration_count(self, val):
        self.key_migration_count = val

    def consistent(self):
        sig = set()
        for instance in self.nodes:
            if not instance.is_master():
                continue
            nodes = instance.nodes()
            slots, names = [], []
            for node in nodes:
                slots.extend(node['slots'])
                names.append(node['name'])
            info = '{}:{}'.format('|'.join(sorted(names)),
                                  ','.join(str(i) for i in sorted(slots)))
            sig.add(hashlib.md5(info).hexdigest())
        return len(sig) == 1

    def healthy(self):
        slots = list(itertools.chain(*[i.slots for i in self.nodes]))
        return len(slots) == self.CLUSTER_HASH_SLOTS and self.consistent()

    def wait(self):
        check = 0
        while not self.consistent():
            time.sleep(1)
            if check == 10:
                raise ClusterNotConsistent('Error: cluster is not consistent')
            check += 1

        if not self.healthy():
            raise ClusterNotHealthy('Error: missing slots')

    def get_node(self, node_id):
        for i in self.nodes:
            if i.name == node_id:
                return i

    def fix_open_slots(self):
        for master in self.masters:
            self.fix_node(master)

    def fix_node(self, node):
        info = node.node_info

        for slot, dst_id in info['migrating'].items():
            dst = self.get_node(dst_id)
            if not dst or slot not in dst.node_info['importing']:
                node.set_slot('STABLE', slot)
                continue

            node.migrate_slot(dst, slot, self)

        for slot, target_id in info['importing'].items():
            src = self.get_node(target_id)
            if not src or slot not in src.node_info['migrating']:
                node.set_slot('STABLE', slot)
                continue

            src.migrate_slot(node, slot, self)

    @failover.on_timeout
    def reshard(self):
        if not self.consistent():
            return

        nodes = [{
                     "node": n,
                     "count": len(n.slots),
                     "need": []
                 } for n in self.masters]

        nodes = self.slot_balance(nodes)

        for n in nodes:
            if not n["need"]:
                continue
            for src, count in n["need"]:
                self.migrate(src, n["node"], count)

    @failover.on_timeout
    def remove_node(self, node):
        if node.is_master():
            self.migrate_node(node)

        self.nodes = [n for n in self.nodes if n.name != node.name]
        masters = self.masters
        masters.sort(key=lambda x: len(x.slaves(x.name)))

        for n in self.nodes:
            if n.is_slave(node.name):
                n.replicate(masters[0].name)
            n.forget(node.name)

        assert not node.slots
        node.reset()

    def add_node(self, master):
        """
        Add node to cluster.
        """
        new = Node.from_uri(master)
        cluster_member = self.nodes[0]
        new.meet(cluster_member.host, cluster_member.port)
        self.nodes.append(new)
        self.wait()

    def fill_slots(self):
        masters = self.masters
        slots = itertools.chain(*[n.slots for n in masters])
        missing = list(set(range(self.CLUSTER_HASH_SLOTS)).difference(slots))

        div = divide(len(missing), len(masters))
        masters.sort(key=lambda x: len(x.slots))

        i = 0
        for count, node in zip(div, masters):
            node.add_slots(*missing[i:count + i])
            i += count

    def bind_slots_force(self):
        masters = self.masters
        slots = itertools.chain(*[n.slots for n in masters])
        missing = list(set(range(self.CLUSTER_HASH_SLOTS)).difference(slots))

        div = divide(len(missing), len(masters))
        masters.sort(key=lambda x: len(x.slots))

        i = 0
        for count, node in zip(div, masters):
            for slot in missing[i:count + i]:
                self.update_slot_mapping(slot, node.name)
            i += count

    def migrate_node(self, src_node):
        nodes = [n for n in self.masters if n.name != src_node.name]
        slot_count = len(src_node.slots)
        if slot_count <= 0:
            return
        slots = divide(slot_count, len(nodes))

        nodes.sort(key=lambda x: len(x.slots))

        for node, count in zip(nodes, slots):
            src, dst = (src_node, node)
            self.migrate(src, dst, count)

    def migrate(self, src, dst, count):
        if count <= 0:
            return

        slots = src.slots
        slots_count = len(slots)
        if count > slots_count:
            count = slots_count

        keys = [(s, src.count_keys_in_slot(s)) for s in slots]
        keys.sort(key=lambda x: x[1])

        for slot, _ in keys[:count]:
            src.migrate_slot(dst, slot, self)

    def update_slot_mapping(self, slot, dst_name):
        for node in self.parent_nodes:
            node.set_slot('NODE', slot, dst_name)

    def print_attempts(self):
        for node in self.nodes:
            self.attempts.extend(node.attempts)
        echo('Length of attempts: {}'.format(len(self.attempts)))
        for exc, group in itertools.groupby(self.attempts,
                                            lambda a: type(a).__name__):
            length = len(list(group))
            echo(
                'Exception: {}, Count: {}'.format(exc, length),
                color='yellow')

    def slot_balance(self, seq):
        amt = self.CLUSTER_HASH_SLOTS
        seq.sort(key=lambda x: x['count'], reverse=True)
        chunks = divide(amt, len(seq))
        pairs = list(zip(seq, chunks))

        i, j = 0, len(pairs) - 1
        while i < j:
            m, count = pairs[i]
            more = m['count'] - count
            if more <= 0:
                i += 1
                continue

            n, count = pairs[j]
            need = count - n['count']
            if need <= 0:
                j -= 1
                continue

            if need < more:
                n['need'].append((m['node'], need))
                n['count'] += need
                m['count'] -= need
                j -= 1
            elif need > more:
                n['need'].append((m['node'], more))
                n['count'] += more
                m['count'] -= more
                i += 1
            else:
                n['need'].append((m['node'], need))
                n['count'] += need
                m['count'] -= more
                j -= 1
                i += 1

        return seq

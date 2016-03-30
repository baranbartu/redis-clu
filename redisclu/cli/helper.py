import argparse
import collections
from redisclu.node import Node
from redisclu.cluster import Cluster
from redisclu.utils import echo, spread, divide


class Context(object):
    def __init__(self, parser=None):
        self.__parser = parser

    def abort(self, message):
        if not self.__parser:
            return

        self.__parser.error(message)


class Command(object):
    def __init__(self, args, func):
        self.arguments = args
        self.parser = None
        self.name = func.__name__
        self.doc = func.__doc__
        self.func = func

    def callback(self, args):
        ctx = Context(self.parser)
        if hasattr(self.func, '__pass_ctx__'):
            self.func(ctx, args)
        else:
            self.func(args)

    @classmethod
    def command(cls, func):
        if not hasattr(func, '__cmd_args__'):
            func.__cmd_args__ = []
        func.__cmd_args__.reverse()
        return cls(func.__cmd_args__, func)

    @classmethod
    def pass_ctx(cls, func):
        func.__pass_ctx__ = True
        return func

    @classmethod
    def argument(cls, *args, **kwargs):
        def deco(func):
            if not hasattr(func, '__cmd_args__'):
                func.__cmd_args__ = []
            func.__cmd_args__.append((args, kwargs))
            return func

        return deco

    def __call__(self):
        self.parser = argparse.ArgumentParser()
        for args, kwargs in self.arguments:
            self.parser.add_argument(*args, **kwargs)
        args = self.parser.parse_args()
        self.callback(args)


class CommandParser(object):
    def __init__(self, *args, **kwargs):
        self.parser = argparse.ArgumentParser(*args, **kwargs)
        self.subparser = self.parser.add_subparsers(title='Subcommands')

    def add_command(self, command):
        parser = self.subparser.add_parser(command.name, help=command.doc)
        command.parser = parser
        for args, kwargs in command.arguments:
            parser.add_argument(*args, **kwargs)
        parser.set_defaults(func=command.callback)

    def run(self):
        args = self.parser.parse_args()
        args.func(args)


command = Command.command
argument = Command.argument
pass_ctx = Command.pass_ctx


class MasterCandidate(object):
    def __init__(self, master):
        self.master = master
        self.unassigned_slots = []

    def __getattr__(self, attr):
        return getattr(self.node, attr)

    def assign_slots(self):
        assert self.unassigned_slots
        for chunk in self.unassigned_slots:
            self.addslots(*range(*chunk))

    def is_enabled(self):
        return self.unassigned_slots


class ClusterCreator(object):
    def __init__(self, masters):
        master_candidates = [Node.from_uri(i) for i in masters]
        self.master_candidates = [MasterCandidate(i) for i in
                                  master_candidates]
        self.masters = []
        self.cluster = None

    def check(self):
        # check pre-requirements
        if len(self.master_candidates) < 2:
            return False
        for master in self.master_candidates:
            if not master.info().get('cluster_enabled'):
                return False
            master.execute_command('select', '0')
            if master.randomkey():
                return False
            if master.cluster_info()['cluster_known_nodes'] != 1:
                return False
        return True

    def initialize_slots(self):
        ips = collections.defaultdict(list)
        for candidate in self.master_candidates:
            ips[candidate.host].append(candidate)
        master_count = len(self.master_candidates)
        self.masters = masters = spread(ips, master_count)
        chunks = self.split_slot(Cluster.CLUSTER_HASH_SLOTS, master_count)
        for master, chunk in zip(masters, chunks):
            master.unassigned_slots.append(chunk)

        self.master_candidates = [i for i in self.master_candidates if
                                  i.is_enabled()]
        self.cluster = Cluster(self.master_candidates)

    def show_cluster_info(self):
        for instance in self.master_candidates:
            echo('M', end='', color='green')
            name_msg = ': {name} {host}:{port}'
            echo(name_msg.format(name=instance.name,
                                 host=instance.host, port=instance.port))
            slot_msg = ','.join(['-'.join([str(s[0]), str(s[1] - 1)])
                                 for s in instance.unassigned_slots])
            echo('\tslots:', slot_msg)

    def set_slots(self):
        for master in self.masters:
            master.assign_slots()

    def join_cluster(self):
        if not self.masters:
            return

        first_master = self.masters[0]
        for master in self.masters[1:]:
            master.meet(first_master.host, first_master.port)

    def assign_config_epoch(self):
        epoch = 1
        for instance in self.masters:
            try:
                instance.set_config_epoch(epoch)
            except:
                pass
            epoch += 1

    def split_slot(self, n, m):
        chunks = divide(n, m)

        res, total = [], 0
        for c in chunks:
            res.append((total, c + total))
            total += c
        return res

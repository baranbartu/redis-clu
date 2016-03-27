import time

from redisclu.cli import helper as cli_helper
from redisclu.cluster import Cluster
from redisclu.node import Node


@cli_helper.command
@cli_helper.argument("masters", nargs='+')
def create(args):
    print args.masters


@cli_helper.command
@cli_helper.argument('cluster')
def status(args):
    print args.cluster


@cli_helper.command
@cli_helper.argument('cluster')
def fix(args):
    print args.cluster


@cli_helper.command
@cli_helper.argument('cluster')
@cli_helper.argument('master')
@cli_helper.pass_ctx
def add(ctx, args):
    """
    add master node to cluster
    """
    cluster = Cluster.from_node(Node.from_uri(args.cluster))

    if not cluster.healthy():
        ctx.abort('Cluster not healthy.')

    cluster.add_master(args.master)
    cluster.reshard()
    cluster.wait()
    cluster.print_attempts()


@cli_helper.command
@cli_helper.argument('cluster')
@cli_helper.argument("masters", nargs='+')
def multi_add(args):
    print args.cluster
    print args.masters


@cli_helper.command
@cli_helper.argument('cluster')
def reshard(args):
    print args.cluster


@cli_helper.command
@cli_helper.argument('cluster')
@cli_helper.argument('node')
def remove(args):
    """
    remove node from cluster
    """
    cluster = Cluster.from_node(Node.from_uri(args.cluster))
    cluster.remove_node(Node.from_uri(args.node))
    cluster.wait()
    cluster.print_attempts()


@cli_helper.command
@cli_helper.argument('slave')
@cli_helper.argument('master')
def replicate(args):
    print args.slave
    print args.master


@cli_helper.command
@cli_helper.argument('cluster')
def destroy(args):
    print args.cluster


def load_commands():
    import commands

    attrs = set(dir(commands)).difference(['load_commands'])
    return filter(lambda f: isinstance(f, cli_helper.Command),
                  map(lambda attr: getattr(commands, attr), attrs))

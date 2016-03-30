import redis
import concurrent.futures

from redisclu.cli import helper as cli_helper
from redisclu.cluster import Cluster
from redisclu.node import Node
from redisclu.utils import echo


@cli_helper.command
@cli_helper.argument('masters', nargs='+')
def create(args):
    print args.masters


@cli_helper.command
@cli_helper.argument('cluster')
def status(args):
    cluster = Cluster.from_node(Node.from_uri(args.cluster))
    dis = []
    for n in cluster.masters:
        slaves = ','.join([s['addr'] for s in n.slaves(n.name)])
        msg = '{} {}:{} {} {}'.format(n.name, n.host, n.port, len(n.slots),
                                      slaves)
        dis.append(msg)
    echo('\n'.join(dis))
    echo('Masters:', len(cluster.masters))
    echo('Slaves:', len(cluster.nodes) - len(cluster.masters))
    covered_slots = sum(len(n.slots) for n in cluster.masters)
    echo('Covered Slots:', covered_slots)
    if covered_slots == cluster.CLUSTER_HASH_SLOTS:
        echo('Cluster is healthy!', color='green')
    else:
        echo('Cluster is not healthy!!!', color='red')
        echo('"rclu fix {}" would be great!'.format(args.cluster),
             color='yellow')

    echo('\n')

    for master in cluster.masters:
        echo(master)
        echo('===========================')
        echo(master.execute_command('info', 'keyspace'))
        echo('\n')


@cli_helper.command
@cli_helper.argument('cluster')
def fix(args):
    cluster = Cluster.from_node(Node.from_uri(args.cluster))
    cluster.fix_open_slots()
    cluster.fill_slots()
    cluster.wait()
    cluster.print_attempts()


@cli_helper.command
@cli_helper.argument('cluster')
@cli_helper.argument('master')
@cli_helper.argument("--keyMigrationCount", default=1)
@cli_helper.pass_ctx
def add(ctx, args):
    """
    add master node to cluster
    """
    cluster = Cluster.from_node(Node.from_uri(args.cluster))
    if not cluster.healthy():
        ctx.abort(
            'Cluster not healthy. Run "rclu fix {}" first'.format(
                args.cluster))
    cluster.set_key_migration_count(int(args.keyMigrationCount))
    cluster.add_node(args.master)
    cluster.reshard()
    cluster.wait()
    cluster.print_attempts()


@cli_helper.command
@cli_helper.argument('cluster')
@cli_helper.argument('masters', nargs='+')
def multi_add(args):
    print args.cluster
    print args.masters


@cli_helper.command
@cli_helper.argument('cluster')
@cli_helper.argument("--keyMigrationCount", default=1)
@cli_helper.pass_ctx
def reshard(ctx, args):
    cluster = Cluster.from_node(Node.from_uri(args.cluster))
    if not cluster.healthy():
        ctx.abort(
            'Cluster not healthy. Run "rclu fix {}" first'.format(
                args.cluster))
    cluster.set_key_migration_count(int(args.keyMigrationCount))
    cluster.reshard()
    cluster.wait()
    cluster.print_attempts()


@cli_helper.command
@cli_helper.argument('cluster')
@cli_helper.argument('node')
@cli_helper.argument("--keyMigrationCount", default=1)
@cli_helper.pass_ctx
def remove(ctx, args):
    """
    remove node from cluster
    """
    cluster = Cluster.from_node(Node.from_uri(args.cluster))
    if not cluster.healthy():
        ctx.abort(
            'Cluster not healthy. Run "rclu fix {}" first'.format(
                args.cluster))
    cluster.set_key_migration_count(int(args.keyMigrationCount))
    cluster.remove_node(Node.from_uri(args.node))
    cluster.wait()
    cluster.print_attempts()


@cli_helper.command
@cli_helper.argument('master')
@cli_helper.argument('slave')
@cli_helper.pass_ctx
def replicate(ctx, args):
    master = Node.from_uri(args.master)
    if not master.is_master():
        ctx.abort('Node {} is not a master.'.format(args.master))
    cluster = Cluster.from_node(master)
    cluster.add_node(args.slave)
    slave = Node.from_uri(args.slave)
    try:
        slave.replicate(master.name)
    except redis.ResponseError as e:
        ctx.abort(str(e))
    cluster.wait()


@cli_helper.command
@cli_helper.argument('cluster')
@cli_helper.argument('--hard', default=0)
def reset(args):
    cluster = Cluster.from_node(Node.from_uri(args.cluster))
    future_to_args = dict()
    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=len(cluster.masters))

    for master in cluster.masters:
        f_args = ()
        future = executor.submit(master.flushall)
        future_to_args.setdefault(future, f_args)

    concurrent.futures.wait(future_to_args)
    executor.shutdown(wait=False)

    if int(args.hard) == 1:
        for node in cluster.nodes:
            node.reset(hard=True)


def load_commands():
    import commands

    attrs = set(dir(commands))
    return filter(lambda f: isinstance(f, cli_helper.Command),
                  map(lambda attr: getattr(commands, attr), attrs))

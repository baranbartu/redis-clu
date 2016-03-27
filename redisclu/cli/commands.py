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
    cluster.add_master(args.master)
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
def reshard(args):
    print args.cluster


@cli_helper.command
@cli_helper.argument('cluster')
@cli_helper.argument('node')
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

    attrs = set(dir(commands))
    return filter(lambda f: isinstance(f, cli_helper.Command),
                  map(lambda attr: getattr(commands, attr), attrs))

from redisclu.cli import helper as cli_helper


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
def add(args):
    print args.cluster
    print args.master


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
@cli_helper.argument('master')
def remove(args):
    print args.master


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

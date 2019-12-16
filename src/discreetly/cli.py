import click
import json
import logging
import discreetly

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("discreetly").addHandler(logging.StreamHandler())


@click.group()
@click.option(
    "-c", "--config", default=None, help="Path to configuration file"
)
@click.option(
    "-p",
    "--profile",
    default="default",
    help="Name of configuration profile, defaults to 'default'",
)
@click.version_option(discreetly.__version__)
@click.pass_context
def cli(ctx, config, profile):
    try:
        ctx.obj = discreetly.Session.create(config, profile)
    except KeyError:
        raise click.BadParameter('Profile "%s" not found' % profile)
    logging.info('Using configuration: "%s"', config)
    logging.info('Using profile: "%s"', profile)


@cli.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.argument("key")
@click.pass_context
def get(ctx, key):
    """GETs the value for the specified KEY"""
    kwargs = {
        ctx.args[i][2:]: ctx.args[i + 1] for i in range(0, len(ctx.args), 2)
    }
    click.echo(ctx.obj.get(key, **kwargs))


@cli.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.argument("key")
@click.argument("value")
@click.pass_context
def set(ctx, key, value):
    """SETs the specified KEY with the specified VALUE"""
    kwargs = {
        ctx.args[i][2:]: ctx.args[i + 1] for i in range(0, len(ctx.args), 2)
    }
    click.echo(json.dumps(kwargs, sort_keys=True, indent=4))

    click.echo(ctx.obj.set(key, value, **kwargs))


@cli.command()
@click.argument("key")
@click.pass_context
def delete(ctx, key):
    """DELETEs the value for the specified KEY"""
    click.echo(ctx.obj.delete(key))


@cli.command()
@click.argument("path")
@click.pass_context
def list(ctx, path):
    """LISTs the keys for the specified PATH"""
    click.echo(ctx.obj.list(path))


@cli.command()
@click.pass_context
def config(ctx):
    """Prints config"""
    click.echo(json.dumps(ctx.obj.config, sort_keys=True, indent=4))


@cli.command()
@click.pass_context
def profile(ctx):
    """Prints profile"""
    click.echo(json.dumps(ctx.obj.profile, sort_keys=True, indent=4))

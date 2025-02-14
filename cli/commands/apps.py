import click
from ..utils import make_request
import json


@click.group()
def apps():
    """Commands for managing apps."""
    pass


@apps.command(name="list")
@click.pass_context
def list_apps(ctx):
    """List all apps."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/apps/"
    response = make_request("GET", url)
    click.echo(f"Apps: {json.dumps(response.json(), indent=4)}")


@apps.command(name="create")
@click.option("--name", required=True, help="Name of the app")
@click.pass_context
def create(ctx, name):
    """Create a new app."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/apps/"
    payload = {
        "app": {
            "name": name,
        }
    }

    response = make_request("POST", url, json=payload)
    click.echo(f"App created successfully: {json.dumps(response.json(), indent=4)}")

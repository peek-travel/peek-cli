import os
from dotenv import load_dotenv
import click
from .commands.apps import apps
from .commands.publishers import publishers
from .commands.versions import versions
from .commands.extendables import extendables
from .commands.services import services

load_dotenv()

ENVIRONMENTS = {
    "stage": os.getenv("STAGE_URL", "https://noreaga.stage.peek.com"),
    "local": os.getenv("LOCAL_URL", "http://noreaga.peek.stack"),
    "prod": os.getenv("PROD_URL", "https://noreaga.peek.com"),
}


@click.group()
@click.option(
    "--env",
    type=click.Choice(["stage", "local", "prod"]),
    default="local",
    help="Environment to use",
)
@click.option(
    "--api-token",
    help="API token for authorization (can also be set via PEEK_API_TOKEN env variable)",
    required=False,
    envvar="PEEK_API_TOKEN",
)
@click.pass_context
def cli(ctx, env, api_token):
    """CLI for interacting with the Peek API."""
    ctx.ensure_object(dict)
    ctx.obj["BASE_URL"] = ENVIRONMENTS[env]
    ctx.obj["ENV"] = env
    ctx.obj["PEEK_API_TOKEN"] = api_token


cli.add_command(apps)
apps.add_command(publishers)
apps.add_command(versions)
apps.add_command(extendables)
apps.add_command(services)

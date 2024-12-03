import click
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default server URLs
ENVIRONMENTS = {
    "stag": os.getenv("STAGE_URL", "https://noreaga.stage.peek.com"),
    "local": os.getenv("LOCAL_URL", "http://noreaga.peek.stack"),
    "prod": os.getenv("PROD_URL", "https://noreaga.peek.com"),
}

@click.group()
@click.option('--env', type=click.Choice(['sandbox', 'local', 'prod']), default='sandbox', help="Environment to use")
@click.pass_context
def cli(ctx, env):
    """CLI for interacting with the Peek API."""
    ctx.ensure_object(dict)
    ctx.obj['BASE_URL'] = ENVIRONMENTS[env]

@cli.command()
@click.argument('name')
@click.argument('email')
@click.argument('website_url')
@click.option('--level', default="internal", help="Level of the publisher")
@click.pass_context
def create_publisher(ctx, name, email, website_url, level):
    """Create a new publisher."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/publishers/"
    payload = {
        "publisher": {
            "name": name,
            "email": email,
            "website_url": website_url,
            "level": level
        }
    }

    print(payload)

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        click.echo(f"Publisher created successfully: {response.json()}")
    except requests.RequestException as e:
        click.echo(f"Error creating publisher: {e}", err=True)

@cli.command()
@click.pass_context
def apps_list(ctx):
    """List all apps."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/apps/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        click.echo(f"Apps: {response.json()}")
    except requests.RequestException as e:
        click.echo(f"Error fetching apps: {e}", err=True)

if __name__ == '__main__':
    cli()
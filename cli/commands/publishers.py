import click
from ..utils import make_request


@click.group()
def publishers():
    """Commands for managing publishers."""
    pass


@publishers.command(name="create")
@click.option("--name", required=True, help="Name of the publisher")
@click.option("--email", required=True, help="Email of the publisher")
@click.option("--website-url", required=True, help="Website URL of the publisher")
@click.option("--level", default="internal", help="Level of the publisher")
@click.pass_context
def create(ctx, name, email, website_url, level):
    """Create a new publisher."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/publishers/"
    payload = {
        "publisher": {
            "name": name,
            "email": email,
            "website_url": website_url,
            "level": level,
        }
    }

    response = make_request("POST", url, json=payload)
    click.echo(f"Publisher created successfully: {response.json()}")

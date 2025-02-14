import click
import json
from ..utils import make_request


@click.group()
def extendables():
    """Commands for managing extendables."""
    pass


@extendables.command(name="list")
@click.pass_context
def list_extendables(ctx):
    """List all extendables."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/extendables/"
    response = make_request("GET", url)
    click.echo(f"Extendables: {json.dumps(response.json(), indent=4)}")


@extendables.command(name="new")
@click.option(
    "--name", required=True, help="Name of the extendable (e.g. extendable@v1)"
)
@click.option("--app-id", required=True, help="ID of the app")
@click.option("--version", required=True, help="Version to update")
@click.pass_context
def new(ctx, name, app_id, version):
    """Get a template for a new extendable configuration."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/extendables"
    response = make_request("GET", url)
    filtered_response = [
        item for item in response.json()["data"] if item["slug"] == name
    ]
    if not filtered_response:
        click.echo(f"Error: Extendable {name} not found")
        return
    new_extendable = filtered_response[0]
    new_extendable["extendable_slug"] = new_extendable["slug"]
    del new_extendable["slug"]

    url = f"{ctx.obj['BASE_URL']}/app-registry/api/apps/{app_id}/versions/{version}/"

    try:
        current_version = make_request("GET", url).json()
        current_version["app_version"] = current_version["data"]
        current_version["app_version"]["configured_extendables"] = [
            {
                "extendable_slug": extendable["slug"],
                "configuration": extendable["configuration"],
            }
            for extendable in current_version["data"]["extendables"]
        ]
        for extendable in current_version["app_version"]["configured_extendables"]:
            del extendable["configuration"]["__type__"]
        del current_version["data"]
        del current_version["app_version"]["extendables"]
        current_version["app_version"]["configured_extendables"].append(new_extendable)
        updated_version = json.dumps(current_version, indent=4)
    except Exception as e:
        raise click.ClickException(f"Error getting current version: {str(e)}")

    edited_text = click.edit(updated_version, extension=".json")

    if edited_text is None:
        raise click.ClickException("Update cancelled - no changes made")

    try:
        final_version = json.loads(edited_text)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON: {str(e)}")

    if click.confirm("Do you want to update this version?"):
        response = make_request("PUT", url, json=final_version)
        click.echo(
            f"Version updated successfully: {json.dumps(response.json(), indent=4)}"
        )
    else:
        raise click.ClickException("Update cancelled")

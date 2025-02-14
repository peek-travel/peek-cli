import click
import json
from ..utils import make_request


@click.group()
def versions():
    """Commands for managing versions."""
    pass


@versions.command(name="create")
@click.option("--app-id", required=True, help="ID of the app")
@click.option("--version", required=True, help="Version to create")
@click.option("--description", required=False, help="Description of the version")
@click.pass_context
def create(ctx, app_id, version, description):
    """Create a new version for an app."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/apps/{app_id}/versions/"
    payload = {
        "app_version": {
            "display_version": version,
            "description": description,
        }
    }
    response = make_request("POST", url, json=payload)
    click.echo(f"Version created successfully: {json.dumps(response.json(), indent=4)}")


@versions.command(name="list")
@click.option("--app-id", required=True, help="ID of the app")
@click.pass_context
def list_versions(ctx, app_id):
    """List all versions for an app."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/apps/{app_id}/versions/"
    response = make_request("GET", url)
    click.echo(f"Versions: {json.dumps(response.json(), indent=4)}")


@versions.command(name="publish")
@click.option("--app-id", required=True, help="ID of the app")
@click.option("--version", required=True, help="Version to publish")
@click.pass_context
def publish(ctx, app_id, version):
    """Publish a version of an app."""
    url = f"{ctx.obj['BASE_URL']}/app-registry/api/apps/{app_id}/versions/{version}/publish"
    response = make_request("POST", url)
    click.echo(
        f"Version published successfully: {json.dumps(response.json(), indent=4)}"
    )


@versions.command(name="edit")
@click.option("--app-id", required=True, help="ID of the app")
@click.option("--version", required=True, help="Version to edit")
@click.pass_context
def edit(ctx, app_id, version):
    """Edit a version of an app."""
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

        del current_version["data"]
        del current_version["app_version"]["extendables"]
        template = json.dumps(current_version, indent=4)
    except Exception as e:
        raise click.ClickException(f"Error getting current version: {str(e)}")

    edited_text = click.edit(template, extension=".json")

    if edited_text is None:
        raise click.ClickException("Update cancelled - no changes made")

    try:
        payload = json.loads(edited_text)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON: {str(e)}")

    if click.confirm("Do you want to update this version?"):
        response = make_request("PUT", url, json=payload)
        click.echo(
            f"Version updated successfully: {json.dumps(response.json(), indent=4)}"
        )
    else:
        raise click.ClickException("Update cancelled")

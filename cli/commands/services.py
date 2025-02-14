import click
from google.cloud import run_v2
from google.cloud.run_v2.types import Container
from google.auth import default
from google.api_core import exceptions
from google.cloud.devtools.cloudbuild_v1.services.cloud_build import CloudBuildClient
from google.cloud.devtools.cloudbuild_v1.types import (
    BuildTrigger,
    GitHubEventsConfig,
    PushFilter,
    Build,
    CreateBuildTriggerRequest,
    Source,
    RepoSource,
)
import subprocess
import shlex


@click.group()
def services():
    """Commands for managing services."""
    pass


@services.command(name="create")
@click.option("--name", help="Name of the service", required=True)
@click.option("--image", help="Image to use for the service", required=True)
@click.option("--app-id", help="App ID to use for the service", required=True)
def create_service(name, image, app_id):
    """Create a new Cloud Run service."""
    # TODO: make region configurable
    # TODO: update to use peek's project ids
    # TODO: support secrets as env variables
    region = "us-central1"
    credentials, default_project = default()
    project_id = default_project

    client = run_v2.ServicesClient(credentials=credentials)
    parent = f"projects/{project_id}/locations/{region}"

    # Format service name according to Cloud Run requirements
    service_id = name.lower().replace(" ", "-")

    try:
        template = run_v2.RevisionTemplate(
            containers=[
                Container(
                    image=image,
                    env=[run_v2.types.EnvVar(name="PEEK_APP_ID", value=app_id)],
                )
            ],
        )

        service = run_v2.Service(
            template=template,
            labels={"peek-app-id": app_id},
        )

        operation = client.create_service(
            parent=parent,
            service=service,
            service_id=service_id,
        )

        service_response = operation.result()

        # set iam policy on service so allUsers can access
        print("policy request")
        print(service_response.name)
        policy_request = {
            "resource": service_response.name,
            "policy": {
                "bindings": [
                    {
                        "role": "roles/run.invoker",
                        "members": ["allUsers"],
                    }
                ],
                "version": 3,
            },
        }

        policy_response = client.set_iam_policy(request=policy_request)
        print(policy_response)

        click.echo("\nService created successfully:")
        click.echo(f"Name: {service_response.name}")
        click.echo(f"URL: {service_response.uri}")

    except exceptions.PermissionDenied:
        raise click.ClickException(
            f"Permission denied. Please ensure you have 'run.services.create' permission for project '{project_id}'\n"
            "You can grant this permission by running:\n"
            f"gcloud projects add-iam-policy-binding {project_id} "
            "--member=user:<your-email> --role=roles/run.developer"
        )
    except exceptions.InvalidArgument as e:
        raise click.ClickException(f"Invalid argument: {str(e)}")
    except Exception as e:
        raise click.ClickException(f"Failed to create service: {str(e)}")


@services.command(name="list")
def list_services():
    """List all Cloud Run services."""
    try:
        location = "us-central1"
        credentials, default_project = default()
        project_id = default_project

        if not project_id:
            raise click.ClickException(
                "No project specified. Please provide --project or set GOOGLE_CLOUD_PROJECT environment variable"
            )

        client = run_v2.ServicesClient(credentials=credentials)
        parent = f"projects/{project_id}/locations/{location}"

        try:
            services = client.list_services(parent=parent)
            click.echo(f"\nCloud Run services in {location}:")
            for service in services:
                click.echo(f"- {service.name} ({service.uid})")
                click.echo(f"  URL: {service.uri}")
                click.echo(f"  Created: {service.create_time}")
                click.echo(f"  Updated: {service.update_time}")
                click.echo("")

        except exceptions.PermissionDenied:
            raise click.ClickException(
                f"Permission denied. Please ensure you have 'run.services.list' permission for project '{project_id}'\n"
                "You can grant this permission by running:\n"
                f"gcloud projects add-iam-policy-binding {project_id} "
                "--member=user:<your-email> --role=roles/run.viewer"
            )
        except exceptions.NotFound:
            raise click.ClickException(
                f"Project '{project_id}' or location '{location}' not found"
            )

    except Exception as e:
        raise click.ClickException(f"Failed to list services: {str(e)}")


@services.command(name="delete")
@click.option("--name", help="Name of the service to delete", required=True)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def delete_service(name, force):
    """Delete a Cloud Run service."""
    region = "us-central1"
    credentials, default_project = default()
    project_id = default_project

    client = run_v2.ServicesClient(credentials=credentials)

    # Format service name according to Cloud Run requirements
    service_id = name.lower().replace(" ", "-")
    service_name = f"projects/{project_id}/locations/{region}/services/{service_id}"

    try:
        if not force:
            if not click.confirm(f"Are you sure you want to delete service '{name}'?"):
                click.echo("Deletion cancelled.")
                return

        operation = client.delete_service(name=service_name)
        operation.result()  # Wait for deletion to complete

        click.echo(f"\nService '{name}' deleted successfully.")

    except exceptions.PermissionDenied:
        raise click.ClickException(
            f"Permission denied. Please ensure you have 'run.services.delete' permission for project '{project_id}'\n"
            "You can grant this permission by running:\n"
            f"gcloud projects add-iam-policy-binding {project_id} "
            "--member=user:<your-email> --role=roles/run.developer"
        )
    except exceptions.NotFound:
        raise click.ClickException(f"Service '{name}' not found in {region}")
    except Exception as e:
        raise click.ClickException(f"Failed to delete service: {str(e)}")


@services.command(name="update-policy")
@click.option("--name", help="Name of the service", required=True)
def update_policy(name):
    """Update the IAM policy for a Cloud Run service."""
    credentials, default_project = default()
    project_id = default_project

    client = run_v2.ServicesClient(credentials=credentials)

    try:
        # set iam policy on service so allUsers can access
        policy_request = {
            "resource": name,
            "policy": {
                "bindings": [
                    {
                        "role": "roles/run.invoker",
                        "members": ["allUsers"],
                    }
                ],
                "version": 3,
            },
        }

        policy_response = client.set_iam_policy(request=policy_request)
        print(policy_response)

        click.echo("\nIAM policy updated successfully:")

    except exceptions.PermissionDenied as e:
        print(e)
        raise click.ClickException(
            f"Permission denied. Please ensure you have 'run.services.setIamPolicy' permission for project '{project_id}'\n"
            "You can grant this permission by running:\n"
            f"gcloud projects add-iam-policy-binding {project_id} "
            "--member=user:<your-email> --role=roles/run.developer"
        )
    except exceptions.InvalidArgument as e:
        raise click.ClickException(f"Invalid argument: {str(e)}")
    except Exception as e:
        raise click.ClickException(f"Failed to update IAM policy: {str(e)}")


@services.command(name="deploy-function")
@click.option("--name", help="Name of the function to deploy", required=True)
@click.option("--directory", help="Directory containing the function", required=True)
@click.option(
    "--base-image",
    help="Base image to use for the function",
    required=True,
    type=click.Choice(
        ["ruby33", "python312", "nodejs22", "go122", "dotnet8", "php83", "java21"]
    ),
)
@click.option(
    "--set-env-vars",
    help="Set environment variables e.g. VAR1=VALUE1,VAR2=VALUE2",
    required=False,
)
@click.option("--app-id", help="App ID to use for the function", required=True)
@click.pass_context
def deploy_function(ctx, name, directory, base_image, set_env_vars, app_id):
    """Deploy a function from a directory."""

    # must install beta extension
    # Construct gcloud command
    cmd = f"""gcloud beta run deploy {name} \
        --source={directory} \
        --function main \
        --base-image={base_image} \
        --allow-unauthenticated \
        --labels=peek-app-id={app_id},env={ctx.obj["ENV"]}
    """
    # only add set_env_vars if it is provided
    if set_env_vars:
        cmd += f" --set-env-vars={set_env_vars}"

    try:
        # Run the command
        click.echo("Deploying function...This could take up to 60 seconds.")
        process = subprocess.Popen(
            shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Stream stderr output
        for line in process.stderr:
            click.echo(line, nl=False, err=True)

        process.wait()  # Wait for the process to complete

        if process.returncode == 0:
            click.echo("Function deployed successfully.")
        else:
            raise click.ClickException("Failed to deploy function")

    except subprocess.CalledProcessError as e:
        click.echo(e.stderr, err=True)
        raise click.ClickException("Failed to deploy function")
    except Exception as e:
        raise click.ClickException(f"Error: {str(e)}")

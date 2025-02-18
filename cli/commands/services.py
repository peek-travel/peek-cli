import click
import os
from google.cloud import run_v2
from google.cloud.devtools import cloudbuild_v1
from google.cloud.devtools.cloudbuild_v1.types import (
    GitHubEventsConfig,
    PushFilter,
    BuildTrigger,
    BuildStep,
)
from google.cloud.run_v2.types import Container
from google.auth import default
from google.api_core import exceptions
import google.api_core.exceptions


@click.group()
def services():
    """Commands for managing services."""
    pass


class IamPolicyManager:
    """IAM policy manager enables unauthenticated access to Cloud Run services."""

    def __init__(self, client):
        self.client = client

    def set_invoker_policy(self, resource_name):
        policy_request = {
            "resource": resource_name,
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
        return self.client.set_iam_policy(request=policy_request)


class CloudBuildTriggerManager:
    """Manages the creation of Cloud Build triggers."""

    def __init__(self, credentials, project_id, region, owner, repo, service_account):
        self.client = cloudbuild_v1.CloudBuildClient(credentials=credentials)
        self.project_id = project_id
        self.region = region
        self.owner = owner
        self.repo = repo
        self.service_account = service_account

    def create_build_trigger(self, name):
        steps = [
            BuildStep(
                id="Build",
                name="gcr.io/cloud-builders/docker",
                args=[
                    "build",
                    "--no-cache",
                    "-t",
                    f"{self.region}-docker.pkg.dev/{self.project_id}/cloud-run-source-deploy/{self.owner}/{self.repo}:$COMMIT_SHA",
                    ".",
                    "-f",
                    "Dockerfile",
                ],
            ),
            BuildStep(
                id="Push",
                name="gcr.io/cloud-builders/docker",
                args=[
                    "push",
                    f"{self.region}-docker.pkg.dev/{self.project_id}/cloud-run-source-deploy/{self.owner}/{self.repo}:$COMMIT_SHA",
                ],
            ),
            BuildStep(
                id="Deploy",
                name="gcr.io/google.com/cloudsdktool/cloud-sdk:slim",
                args=[
                    "gcloud",
                    "run",
                    "deploy",
                    name,
                    f"--image={self.region}-docker.pkg.dev/{self.project_id}/cloud-run-source-deploy/{self.owner}/{self.repo}:$COMMIT_SHA",
                    f"--labels=managed-by=gcp-cloud-build-deploy-cloud-run,commit-sha=$COMMIT_SHA,gcb-build-id=$BUILD_ID,peek-app-id={name}",
                    f"--region={self.region}",
                ],
            ),
        ]

        trigger = BuildTrigger(
            name=name,
            github=GitHubEventsConfig(
                owner=self.owner,
                name=self.repo,
                push=PushFilter(branch="main"),
            ),
            # Gotta have this or API call will fail with invalid argument
            service_account=self.service_account,
            substitutions={
                "_SERVICE_NAME": name,
                "_DEPLOY_REGION": self.region,
                "_AR_HOSTNAME": f"{self.region}-docker.pkg.dev",
                "_PLATFORM": "managed",
            },
        )
        trigger.autodetect = True
        trigger.build = cloudbuild_v1.Build(
            steps=steps,
            # Need this or API call will fail
            options=cloudbuild_v1.BuildOptions(
                logging="CLOUD_LOGGING_ONLY",
            ),
        )

        request = cloudbuild_v1.CreateBuildTriggerRequest(
            project_id=self.project_id,
            trigger=trigger,
        )

        try:
            response = self.client.create_build_trigger(request=request)

            request = cloudbuild_v1.RunBuildTriggerRequest(
                project_id=self.project_id,
                trigger_id=response.id,
                source=cloudbuild_v1.RepoSource(
                    branch_name="main",
                ),
            )

            # Make the request to trigger the first build
            operation = self.client.run_build_trigger(request=request)

            print("Waiting for operation to complete...")
            operation.result()

            return response
        except google.api_core.exceptions.AlreadyExists:
            raise click.ClickException(f"Build trigger '{name}' already exists")
        except google.api_core.exceptions.GoogleAPICallError as e:
            raise click.ClickException(f"Failed to create build trigger: {str(e)}")


class CloudRunServiceManager:
    """Manages the creation of Cloud Run services."""

    def __init__(self, credentials=None):
        if credentials is None:
            credentials, project_id = default()
            region = os.getenv("GCP_REGION")
            if not region:
                raise click.ClickException("GCP_REGION is not set")

        self.client = run_v2.ServicesClient(credentials=credentials)
        self.parent = f"projects/{project_id}/locations/{region}"

    def create_service(self, name, image=None):
        containers = []
        if image:
            container = Container(image=image)
            if name:
                container.env = [run_v2.types.EnvVar(name="PEEK_APP_ID", value=name)]
            containers.append(container)
        else:
            # uses a place holder image since you can't create a service without an image
            # and we don't have an image yet because we haven't created and run the build trigger
            # smells like a bug, but it works for now.
            # we might revisit this and first create a build so that we have an image, then create a service, then create the build trigger
            container = Container(
                image="us-docker.pkg.dev/cloudrun/container/hello",
            )
            containers.append(container)

        template = run_v2.RevisionTemplate(
            containers=containers,
        )

        service = run_v2.Service(
            template=template,
            labels={"peek-app-id": name},
        )

        try:
            operation = self.client.create_service(
                parent=self.parent,
                service=service,
                service_id=name,
            )

            return operation.result()
        except google.api_core.exceptions.AlreadyExists:
            raise click.ClickException(f"Service '{name}' already exists")
        except google.api_core.exceptions.GoogleAPICallError as e:
            raise click.ClickException(f"Failed to create service: {str(e)}")


@services.command(name="create")
@click.option(
    "--repository",
    help="Github repository to use ex. peek-travel/peek-cli",
    required=True,
)
@click.option("--app-id", help="App ID to use for the service", required=True)
def create_service(repository, app_id):
    """Create a service from a GitHub repo and enable autodeploy."""
    credentials, default_project = default()
    project_id = default_project

    owner = repository.split("/")[0]
    repo = repository.split("/")[1]
    name = app_id.replace("_", "-") + "-" + repo
    service_account = os.getenv("GCP_SERVICE_ACCOUNT")
    region = os.getenv("GCP_REGION")

    if not service_account:
        raise click.ClickException("GCP_SERVICE_ACCOUNT is not set")

    if not region:
        raise click.ClickException("GCP_REGION is not set")

    # Create service without initial image
    service_manager = CloudRunServiceManager()
    service_response = service_manager.create_service(name)

    # Set IAM policy to enable unauthenticated access to the service via http
    IamPolicyManager(service_manager.client).set_invoker_policy(service_response.name)

    # Create build trigger to autodeploy from GitHub
    build_trigger_manager = CloudBuildTriggerManager(
        credentials, project_id, region, owner, repo, service_account
    )
    build_trigger_manager.create_build_trigger(name)

    click.echo(f"Build completed successfully!")
    click.echo("\nService created successfully:")
    click.echo(f"Name: {service_response.name}")
    click.echo(f"URL: {service_response.uri}")


@services.command(name="deploy-image")
@click.option("--name", help="Name of the service", required=True)
@click.option("--image", help="Image to use for the service", required=True)
@click.option("--app-id", help="App ID to use for the service", required=True)
def deploy_image(name, image, app_id):
    """Deploy an existing Docker image to Cloud Run."""
    # Format service name according to Cloud Run requirements
    service_id = name.lower().replace(" ", "-")

    # Use the new class to create the service
    service_manager = CloudRunServiceManager()
    service_response = service_manager.create_service(
        service_id, image=image, app_id=app_id
    )

    # Set IAM policy to enable unauthenticated access
    IamPolicyManager(service_manager.client).set_invoker_policy(service_response.name)

    click.echo("\nService created successfully:")
    click.echo(f"Name: {service_response.name}")
    click.echo(f"URL: {service_response.uri}")


@services.command(name="list")
def list_services():
    """List all Cloud Run services."""
    try:
        location = os.getenv("GCP_REGION")
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
    region = os.getenv("GCP_REGION")
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
        # Set IAM policy using the new class
        iam_policy_manager = IamPolicyManager(client)
        policy_response = iam_policy_manager.set_invoker_policy(name)
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

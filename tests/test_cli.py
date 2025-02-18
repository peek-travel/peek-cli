import pytest
import responses
from click.testing import CliRunner
from cli import cli
import json


@pytest.fixture
def runner():
    return CliRunner()


@responses.activate
def test_apps_publishers_create(runner, monkeypatch):
    # Mock environment variables
    monkeypatch.setenv("ADMIN_BASIC_AUTH_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_BASIC_AUTH_PASSWORD", "admin")

    responses.add(
        responses.POST,
        "http://noreaga.peek.stack/app-registry/api/publishers/",
        json={"id": 1, "name": "Test Publisher"},
        status=201,
        match=[
            responses.matchers.header_matcher(
                {
                    "Content-Type": "application/json",
                    "Authorization": "Basic YWRtaW46YWRtaW4=",  # Correct base64 encoding of "admin:admin"
                }
            )
        ],
    )
    result = runner.invoke(
        cli,
        [
            "--env",
            "local",
            "apps",
            "publishers",
            "create",
            "--name",
            "Test Publisher",
            "--email",
            "test@example.com",
            "--website-url",
            "http://test.com",
        ],
    )
    print(result.output)
    assert result.exit_code == 0
    assert "Publisher created successfully" in result.output


def test_invalid_env(runner):
    result = runner.invoke(cli, ["--env", "invalid_env", "apps", "list"])
    assert result.exit_code != 0


@responses.activate
def test_apps_list(runner):
    # Mock API token
    api_token = "test_token"

    responses.add(
        responses.GET,
        "http://noreaga.peek.stack/app-registry/api/apps/",
        json={"apps": [{"id": 1, "name": "Test App"}]},
        status=200,
        match=[
            responses.matchers.header_matcher(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_token}",
                }
            )
        ],
    )

    result = runner.invoke(
        cli, ["--env", "local", "--api-token", api_token, "apps", "list"]
    )
    assert result.exit_code == 0
    assert "Apps:" in result.output


@responses.activate
def test_api_request_failure(runner, monkeypatch):
    # Mock environment variables for auth
    monkeypatch.setenv("ADMIN_BASIC_AUTH_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_BASIC_AUTH_PASSWORD", "admin")

    error_message = "Internal server error occurred"
    responses.add(
        responses.POST,
        "http://noreaga.peek.stack/app-registry/api/publishers/",
        json={"error": error_message},
        status=500,
    )

    result = runner.invoke(
        cli,
        [
            "--env",
            "local",
            "apps",
            "publishers",
            "create",
            "--name",
            "Test Publisher",
            "--email",
            "test@example.com",
            "--website-url",
            "http://test.com",
        ],
    )
    assert result.exit_code != 0
    assert f"Server error occurred (Status: 500): {error_message}" in result.output


def test_apps_publishers_create_missing_required_options(runner):
    result = runner.invoke(cli, ["--env", "local", "apps", "publishers", "create"])
    assert result.exit_code != 0
    assert "Missing option '--name'" in result.output


@responses.activate
def test_apps_create(runner):
    # Mock API token
    api_token = "test_token"

    responses.add(
        responses.POST,
        "http://noreaga.peek.stack/app-registry/api/apps/",
        json={"id": 1, "name": "My App"},
        status=201,
        match=[
            responses.matchers.header_matcher(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_token}",
                }
            ),
            responses.matchers.json_params_matcher({"app": {"name": "My App"}}),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "--env",
            "local",
            "--api-token",
            api_token,
            "apps",
            "create",
            "--name",
            "My App",
        ],
    )
    assert result.exit_code == 0
    assert "App created successfully" in result.output


def test_apps_create_missing_name(runner):
    result = runner.invoke(cli, ["--env", "local", "apps", "create"])
    assert result.exit_code != 0
    assert "Missing option '--name'" in result.output


@responses.activate
def test_versions_publish(runner):
    # Mock API token
    api_token = "test_token"
    app_id = "123"
    version = "456"

    responses.add(
        responses.POST,
        f"http://noreaga.peek.stack/app-registry/api/apps/{app_id}/versions/{version}/publish",
        json={"status": "published", "version": version},
        status=200,
        match=[
            responses.matchers.header_matcher(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_token}",
                }
            ),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "--env",
            "local",
            "--api-token",
            api_token,
            "apps",
            "versions",
            "publish",
            "--app-id",
            app_id,
            "--version",
            version,
        ],
    )
    assert result.exit_code == 0
    assert "Version published successfully" in result.output


def test_versions_publish_missing_options(runner):
    result = runner.invoke(cli, ["--env", "local", "apps", "versions", "publish"])
    assert result.exit_code != 0
    assert "Missing option '--app-id'" in result.output


@responses.activate
def test_apps_list_with_env_token(runner, monkeypatch):
    # Set API token via environment variable
    api_token = "env_token"
    monkeypatch.setenv("PEEK_API_TOKEN", api_token)

    responses.add(
        responses.GET,
        "http://noreaga.peek.stack/app-registry/api/apps/",
        json={"apps": [{"id": 1, "name": "Test App"}]},
        status=200,
        match=[
            responses.matchers.header_matcher(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_token}",
                }
            )
        ],
    )

    result = runner.invoke(cli, ["--env", "local", "apps", "list"])
    assert result.exit_code == 0
    assert "Apps:" in result.output


@responses.activate
def test_cli_token_precedence(runner, monkeypatch):
    # Set both environment and CLI tokens
    env_token = "env_token"
    cli_token = "cli_token"
    monkeypatch.setenv("PEEK_API_TOKEN", env_token)

    responses.add(
        responses.GET,
        "http://noreaga.peek.stack/app-registry/api/apps/",
        json={"apps": [{"id": 1, "name": "Test App"}]},
        status=200,
        match=[
            responses.matchers.header_matcher(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {cli_token}",  # Should use CLI token
                }
            )
        ],
    )

    result = runner.invoke(
        cli, ["--env", "local", "--api-token", cli_token, "apps", "list"]
    )
    assert result.exit_code == 0
    assert "Apps:" in result.output


@responses.activate
def test_versions_list(runner):
    # Mock API token
    api_token = "test_token"
    app_id = "123"

    mock_response = {
        "versions": [
            {
                "id": 1,
                "display_version": "1.0.0",
                "description": "Initial version",
                "status": "draft",
            },
            {
                "id": 2,
                "display_version": "1.1.0",
                "description": "Bug fixes",
                "status": "published",
            },
        ]
    }

    responses.add(
        responses.GET,
        f"http://noreaga.peek.stack/app-registry/api/apps/{app_id}/versions/",
        json=mock_response,
        status=200,
        match=[
            responses.matchers.header_matcher(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_token}",
                }
            ),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "--env",
            "local",
            "--api-token",
            api_token,
            "apps",
            "versions",
            "list",
            "--app-id",
            app_id,
        ],
    )
    assert result.exit_code == 0
    assert "Versions:" in result.output
    # Verify some of the mock data appears in the output
    assert "1.0.0" in result.output
    assert "1.1.0" in result.output
    assert "published" in result.output


def test_versions_list_missing_app_id(runner):
    result = runner.invoke(cli, ["--env", "local", "apps", "versions", "list"])
    assert result.exit_code != 0
    assert "Missing option '--app-id'" in result.output


@responses.activate
def test_versions_edit_with_editor(runner, monkeypatch):
    api_token = "test_token"
    app_id = "123"
    version = "1.0.0"

    # Mock the current version response
    current_version = {
        "data": {
            "description": "Old description",
            "screenshots": [],
            "categories": [],
            "extendables": [],  # Add empty extendables array
        }
    }

    # Mock the updated version
    updated_version = {
        "app_version": {
            "description": "New description",
            "screenshots": ["https://example.com/new.jpg"],
            "categories": ["New Category"],
            "configured_extendables": [],  # Add empty configured_extendables array
        }
    }

    # Mock the GET request for current version
    responses.add(
        responses.GET,
        f"http://noreaga.peek.stack/app-registry/api/apps/{app_id}/versions/{version}/",
        json=current_version,
        status=200,
    )

    # Mock the PUT request for update
    responses.add(
        responses.PUT,
        f"http://noreaga.peek.stack/app-registry/api/apps/{app_id}/versions/{version}/",
        json=updated_version,
        status=200,
        match=[
            responses.matchers.header_matcher(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_token}",
                }
            ),
            responses.matchers.json_params_matcher(updated_version),
        ],
    )

    # Mock the editor to return our updated version
    def mock_editor(text, extension):
        return json.dumps(updated_version, indent=4)

    # Mock the confirmation to return True
    def mock_confirm(prompt):
        return True

    monkeypatch.setattr("click.edit", mock_editor)
    monkeypatch.setattr("click.confirm", mock_confirm)

    result = runner.invoke(
        cli,
        [
            "--env",
            "local",
            "--api-token",
            api_token,
            "apps",
            "versions",
            "edit",
            "--app-id",
            app_id,
            "--version",
            version,
        ],
    )

    assert result.exit_code == 0
    assert "Version updated successfully" in result.output


@responses.activate
def test_versions_edit_invalid_json(runner, monkeypatch):
    api_token = "test_token"
    app_id = "123"
    version = "1.0.0"

    # Mock the current version response
    current_version = {
        "data": {
            "description": "Old description",
            "screenshots": [],
            "categories": [],
            "extendables": [],
        }
    }

    # Mock the GET request
    responses.add(
        responses.GET,
        f"http://noreaga.peek.stack/app-registry/api/apps/{app_id}/versions/{version}/",
        json=current_version,
        status=200,
    )

    # Mock the editor to return invalid JSON
    def mock_editor(text, extension):
        return "{ invalid json }"

    monkeypatch.setattr("click.edit", mock_editor)

    result = runner.invoke(
        cli,
        [
            "--env",
            "local",
            "--api-token",
            api_token,
            "apps",
            "versions",
            "edit",
            "--app-id",
            app_id,
            "--version",
            version,
        ],
    )

    assert result.exit_code != 0
    assert "Invalid JSON" in result.output


@responses.activate
def test_versions_edit_cancelled(runner, monkeypatch):
    api_token = "test_token"
    app_id = "123"
    version = "1.0.0"

    # Mock the current version response
    current_version = {
        "data": {
            "description": "Old description",
            "screenshots": [],
            "categories": [],
            "extendables": [],
        }
    }

    # Mock the GET request
    responses.add(
        responses.GET,
        f"http://noreaga.peek.stack/app-registry/api/apps/{app_id}/versions/{version}/",
        json=current_version,
        status=200,
    )

    # Mock the editor to return None (simulating no changes)
    def mock_editor(text, extension):
        return None

    monkeypatch.setattr("click.edit", mock_editor)

    result = runner.invoke(
        cli,
        [
            "--env",
            "local",
            "--api-token",
            api_token,
            "apps",
            "versions",
            "edit",
            "--app-id",
            app_id,
            "--version",
            version,
        ],
    )

    assert result.exit_code != 0
    assert "Update cancelled" in result.output


@responses.activate
def test_extendables_new(runner, monkeypatch):
    api_token = "test_token"
    app_id = "123"
    version = "1.0.0"
    extendable_name = "test_extendable@v1"

    # Mock the extendables list response
    mock_extendables_response = {
        "data": [
            {
                "slug": extendable_name,
                "name": "Test Extendable",
                "template": {"url": "https://example.com/webhook"},
            }
        ]
    }

    # Mock the current version response
    mock_version_response = {
        "data": {
            "description": "Current version",
            "extendables": [],
        }
    }

    # Mock the updated version response
    mock_updated_version = {
        "app_version": {
            "description": "Current version",
            "configured_extendables": [
                {
                    "extendable_slug": extendable_name,
                    "configuration": {"url": "https://example.com/webhook"},
                }
            ],
        }
    }

    # Mock the GET requests
    responses.add(
        responses.GET,
        "http://noreaga.peek.stack/app-registry/api/extendables",
        json=mock_extendables_response,
        status=200,
    )

    responses.add(
        responses.GET,
        f"http://noreaga.peek.stack/app-registry/api/apps/{app_id}/versions/{version}/",
        json=mock_version_response,
        status=200,
    )

    # Mock the PUT request
    responses.add(
        responses.PUT,
        f"http://noreaga.peek.stack/app-registry/api/apps/{app_id}/versions/{version}/",
        json=mock_updated_version,
        status=200,
    )

    # Mock the editor to return the template
    def mock_editor(text, extension):
        return text

    # Mock the confirmation to return True
    def mock_confirm(prompt):
        return True

    monkeypatch.setattr("click.edit", mock_editor)
    monkeypatch.setattr("click.confirm", mock_confirm)

    result = runner.invoke(
        cli,
        [
            "--env",
            "local",
            "--api-token",
            api_token,
            "apps",
            "extendables",
            "new",
            "--name",
            extendable_name,
            "--app-id",
            app_id,
            "--version",
            version,
        ],
    )
    assert result.exit_code == 0
    assert extendable_name in result.output


def test_extendables_new_missing_name(runner):
    result = runner.invoke(cli, ["--env", "local", "apps", "extendables", "new"])
    assert result.exit_code != 0
    assert "Missing option '--name'" in result.output

import pytest
import responses
from click.testing import CliRunner
from cli import cli

@pytest.fixture
def runner():
    return CliRunner()

@responses.activate
def test_create_publisher(runner):
    responses.add(
        responses.POST,
        "http://sandbox.example.com/app-registry/api/publishers/",
        json={"id": 1, "name": "Test Publisher"},
        status=201
    )
    result = runner.invoke(cli, ["--env", "sandbox", "create-publisher", "Test Publisher", "test@example.com", "http://test.com"])
    assert result.exit_code == 0
    assert "Publisher created successfully" in result.output

def test_invalid_env(runner):
    result = runner.invoke(cli, ["--env", "invalid_env", "apps-list"])
    assert result.exit_code != 0
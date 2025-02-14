import click
import requests
import os


def make_request(method, url, **kwargs):
    """Make an authenticated request."""
    kwargs.setdefault("headers", {})["Content-Type"] = "application/json"

    # Use basic auth for publisher endpoints, bearer token for others
    if "/app-registry/api/publishers/" in url:
        username, password = get_auth()
        kwargs["auth"] = (username, password)
    else:
        if not click.get_current_context().obj.get("PEEK_API_TOKEN"):
            raise click.ClickException(
                "API token is required. Please provide it using --api-token"
            )
        kwargs["headers"][
            "Authorization"
        ] = f"Bearer {click.get_current_context().obj['PEEK_API_TOKEN']}"

    try:
        response = requests.request(method, url, **kwargs)

        # Try to get error message from response
        error_msg = None
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = (
                    error_data.get("error")
                    or error_data.get("message")
                    or str(error_data)
                )
            except (ValueError, AttributeError):
                error_msg = response.text if response.text else None

        if response.status_code == 401:
            msg = "Authentication failed. Please check your credentials."
            if error_msg:
                msg += f" Error: {error_msg}"
            raise click.ClickException(msg)
        elif response.status_code == 403:
            msg = "Permission denied. You don't have access to this resource."
            if error_msg:
                msg += f" Error: {error_msg}"
            raise click.ClickException(msg)
        elif response.status_code == 404:
            msg = "Resource not found. Please check the URL and try again."
            if error_msg:
                msg += f" Error: {error_msg}"
            raise click.ClickException(msg)
        elif response.status_code >= 400 and response.status_code < 500:
            msg = f"Request failed (Status: {response.status_code})"
            if error_msg:
                msg += f": {error_msg}"
            raise click.ClickException(msg)
        elif response.status_code >= 500:
            msg = f"Server error occurred (Status: {response.status_code})"
            if error_msg:
                msg += f": {error_msg}"
            msg += ". Please try again later."
            raise click.ClickException(msg)

        response.raise_for_status()
        return response
    except requests.ConnectionError:
        raise click.ClickException(
            f"Failed to connect to {url}. Please check your network connection and the server URL."
        )
    except requests.Timeout:
        raise click.ClickException("Request timed out. Please try again.")
    except requests.RequestException as e:
        raise click.ClickException(f"Request failed: {str(e)}")


def get_auth():
    """Get authentication credentials from environment variables."""
    username = os.getenv("ADMIN_BASIC_AUTH_USERNAME")
    password = os.getenv("ADMIN_BASIC_AUTH_PASSWORD")
    if not username or not password:
        raise click.ClickException(
            "Missing authentication credentials. Please set ADMIN_BASIC_AUTH_USERNAME and ADMIN_BASIC_AUTH_PASSWORD environment variables."
        )
    return username, password

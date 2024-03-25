from __future__ import annotations

import traceback
import typing
from dataclasses import dataclass

import click
import requests

from sleuth.service import get_latest_deploy

if typing.TYPE_CHECKING:
    from sleuth.cli import Context


@dataclass
class DeploymentContext:
    root: Context
    organization: str
    deployment: str


@click.command()
@click.option("-o", "--organization", required=True, help="the Sleuth organization slug")
@click.option("-d", "--deployment", required=True, help="the Sleuth deployment slug")
@click.option("-e", "--environment", default="production", help="the Sleuth environment slug")
@click.argument(
    "health",
    required=True,
    type=click.Choice(choices=("healthy", "ailing", "unhealthy", "reset"), case_sensitive=False),
)
@click.pass_obj
def set_health(ctx: Context, organization, deployment, environment, health):
    """Validate a Sleuth actions rules.yml file"""

    deployment_context = DeploymentContext(ctx, organization, deployment)

    try:
        deploy = get_latest_deploy(ctx.baseurl, ctx.api_key, organization, deployment, environment)
        success = set_deploy_health(deployment_context, deploy.slug, health)
    except Exception as e:
        traceback.print_exc(e)
        raise click.ClickException(str(e))

    if success:
        click.echo(f"Health set successfully: {deployment_context.root.baseurl}{deploy.url}")
    else:
        click.echo("ERROR: Health not set")


def set_deploy_health(context: DeploymentContext, deploy: str, health: str) -> bool:
    if health.lower() != "reset":
        health = health.upper()
    query = f"""
            mutation {{
                setHealth(orgSlug:"{context.organization}", deploymentSlug:"{context.deployment}", deploySlug:"{deploy}", health:"{health}") {{
                    success
                }}
            }}
            """  # noqa
    headers = {"AUTHORIZATION": f"Bearer {context.root.api_key}"}
    resp = requests.post(
        f"{context.root.baseurl}/graphql",
        json=dict(query=query),
        headers=headers,
    )
    if resp.status_code == 401:
        print(f" Response: {resp.text}")
        raise ValueError("Unable to authenticate to Sleuth")
    elif resp.status_code != 200:
        raise ValueError(f"Unexpected response: {resp.text}")

    data = resp.json()
    if data.get("errors"):
        raise ValueError(f"Errors in response: {data['errors']}")

    return resp.json()["data"]["setHealth"]["success"]

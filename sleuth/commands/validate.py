from __future__ import annotations

import json
import typing
from dataclasses import dataclass

import click
import requests

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
@click.argument("path", required=True)
@click.pass_obj
def validate(ctx: Context, organization, deployment, path):
    """Validate a Sleuth actions rules.yml file"""

    deployment_context = DeploymentContext(ctx, organization, deployment)
    try:
        rules = validate_rules(deployment_context, path)["validateRules"]["rules"]
    except Exception as e:
        raise click.ClickException(str(e))

    click.echo(f"Validated {len(rules)} rule(s)")


def validate_rules(context: DeploymentContext, path: str) -> typing.Dict:
    operations = {
        "query": f"""
            mutation ($file: Upload!) {{
                validateRules(orgSlug:"{context.organization}", deploymentSlug:"{context.deployment}", file: $file) {{
                    rules {{
                        title
                    }}
                }}
            }}
            """,
        "variables": {"file": None},
    }
    values = {
        "operations": json.dumps(operations),
        "map": json.dumps({"0": ["variables.file"]}),
    }
    files = {"0": open(path, "rb")}
    headers = {"AUTHORIZATION": f"Bearer {context.root.api_key}"}
    resp = requests.post(
        f"{context.root.baseurl}/graphql",
        data=values,
        files=files,
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

    return resp.json()["data"]

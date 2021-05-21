from dataclasses import dataclass

import click

from sleuth.commands.deploy import deploy
from sleuth.version import version


@dataclass
class Context:
    baseurl: str
    api_key: str


@click.group()
@click.version_option(version)
@click.option("-k", "--api-key", required=True, help="the Sleuth API key")
@click.option("--baseurl", default="https://app.sleuth.io", help="The Sleuth base URL")
@click.pass_context
def main(ctx, api_key, baseurl):
    ctx.obj = Context(baseurl=baseurl, api_key=api_key)


main.add_command(deploy)

if __name__ == "__main__":
    main()
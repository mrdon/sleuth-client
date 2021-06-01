from dataclasses import dataclass

import click

from sleuth.commands.deploy import deploy
from sleuth.commands.set_health import set_health
from sleuth.commands.validate import validate
from sleuth.version import version


@dataclass
class Context:
    baseurl: str
    api_key: str


@click.group()
@click.version_option(version)
@click.option("-k", "--api-key", required=True, help="the Sleuth API key")
@click.option("--baseurl", default="https://app.sleuth.io", help="The Sleuth base URL", hidden=True)
@click.pass_context
def main(ctx, api_key, baseurl):
    ctx.obj = Context(baseurl=baseurl, api_key=api_key)


main.add_command(deploy)
main.add_command(validate)
main.add_command(set_health)

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()

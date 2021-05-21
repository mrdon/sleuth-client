from __future__ import annotations

import typing
from dataclasses import dataclass
from time import sleep

import click
from git import Commit
from git import Repo

from sleuth.models import RemoteCommit
from sleuth.models import RemoteFile
from sleuth.service import get_commit_list
from sleuth.service import get_files_list
from sleuth.service import get_latest_revision
from sleuth.service import send_deployment


if typing.TYPE_CHECKING:
    from sleuth.cli import Context


@dataclass
class DeploymentContext:
    root: Context
    organization: str
    deployment: str
    environment: str
    commit_url_pattern: str
    file_url_pattern: str


@click.command()
@click.option("-o", "--organization", required=True, help="the Sleuth organization slug")
@click.option("-d", "--deployment", required=True, help="the Sleuth deployment slug")
@click.option("-e", "--environment", default="production", help="the Sleuth environment slug")
@click.option(
    "--commit-url-pattern",
    default="https://example.com/REVISION",
    help="the commit URL pattern to use for linking, e.g. 'https://server/REVISION'",
)
@click.option(
    "--file-url-pattern",
    default="https://example.com/REVISION/PATH",
    help="the file URL pattern to use for linking, e.g. 'https://server/REVISION/PATH'",
)
@click.argument("git_path", required=False)
@click.pass_obj
def deploy(ctx: Context, organization, deployment, environment, commit_url_pattern, file_url_pattern, git_path):
    """Register a deploy using information from a local git repository"""

    repo = Repo(git_path)
    latest_revision = get_latest_revision(ctx.baseurl, ctx.api_key, organization, deployment, environment)
    head_commit = repo.commit()

    deployment_context = DeploymentContext(
        ctx, organization, deployment, environment, commit_url_pattern, file_url_pattern
    )
    if not latest_revision:
        if head_commit.parents:
            parent: Commit = head_commit.parents[0]
            click.echo("Sending initial state prior to the first deployment")

            send_deployment(
                deployment_context,
                parent,
                [RemoteCommit(commit_url_pattern, parent)],
                [RemoteFile(file_url_pattern, parent.hexsha, "ignored")],
            )
            latest_revision = parent.hexsha
            # This is a terrible hack because we can't detect whether the root deploy has been processed or not
            sleep(5)
        else:
            click.echo("Only one commit detected, so you won't see anything in Sleuth until there are two")
            click.echo("Sending initial state prior to the first deployment")

            send_deployment(
                deployment_context,
                head_commit,
                [RemoteCommit(commit_url_pattern, head_commit)],
                [RemoteFile(file_url_pattern, head_commit.hexsha, "ignored")],
            )
            return

    latest_commit = repo.commit(latest_revision)
    click.echo(f"Determining differences from {latest_commit.hexsha} to {head_commit.hexsha}")
    commits = get_commit_list(deployment_context, head_commit, latest_commit, repo)
    files = get_files_list(deployment_context, head_commit, latest_commit)

    send_deployment(deployment_context, head_commit, commits, files)

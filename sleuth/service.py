from __future__ import annotations

import typing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set

import requests
from git import Commit
from git import Diff
from git import Repo

from sleuth.models import RemoteCommit
from sleuth.models import RemoteFile

if typing.TYPE_CHECKING:
    from .commands.deploy import DeploymentContext


@dataclass
class DeployInfo:
    slug: str
    revision: str
    url: str


def get_latest_deploy(url: str, token: str, org: str, deployment: str, environment: str) -> Optional[DeployInfo]:
    query = f"""
{{
    deployment(orgSlug:"{org}", deploymentSlug:"{deployment}") {{
        ... on CodeChangeSource {{
            latestChange(environmentSlug:"{environment}") {{
                revision
                slug
                url
            }}
        }}
    }}
}}
    """
    headers = {"AUTHORIZATION": f"apikey {token}"}
    resp = requests.get(f"{url}/graphql", json=dict(query=query), headers=headers)
    if resp.status_code == 401:
        raise ValueError("Unable to authenticate to Sleuth")

    body = resp.json()
    if body.get("errors"):
        raise ValueError(f"Errors retrieving latest deployment: {body['errors']}")

    deployment = resp.json()["data"]["deployment"]
    change = deployment["latestChange"] or {}
    if change:
        return DeployInfo(slug=change["slug"], revision=change["revision"], url=change["url"])
    else:
        return None


def list_paths(root_tree, path=Path(".")):
    for blob in root_tree.blobs:
        yield path / blob.name
    for tree in root_tree.trees:
        yield from list_paths(tree, path / tree.name)


def get_commit_list(args, head_commit: Commit, latest_commit: Commit, repo: Repo) -> List[RemoteCommit]:
    result: List[RemoteCommit] = []
    commit_range = "%s...%s" % (latest_commit.hexsha, head_commit.hexsha)
    commit_list = list(repo.iter_commits(commit_range))
    commit_list.reverse()
    last_commit = latest_commit
    for commit in commit_list:
        diff_list: List[Diff] = last_commit.diff(commit.hexsha)
        rcommit = RemoteCommit(args.commit_url_pattern, commit)
        rcommit.files.update(_get_files_in_diff_list(diff_list))
        result.append(rcommit)
        last_commit = commit
    return result


def _get_files_in_diff_list(diff_list: Iterable[Diff]) -> Set[str]:
    result = set()
    for diff in diff_list:
        if diff.a_path:
            result.add(diff.a_path)
        if diff.b_path:
            result.add(diff.b_path)
    return result


def get_files_list(args, head_commit: Commit, latest_commit: Commit) -> List[RemoteFile]:
    diff_list = head_commit.diff(latest_commit.hexsha)
    return [
        RemoteFile(args.file_url_pattern, path=name, revision=head_commit.hexsha)
        for name in _get_files_in_diff_list(diff_list)
    ]


def send_deployment(
    context: DeploymentContext, head_commit: Commit, commits: List[RemoteCommit], files: List[RemoteFile]
):
    body = {
        "sha": head_commit.hexsha,
        "environment": context.environment,
        "date": datetime.utcnow().isoformat(),
        "commits": [c.to_json() for c in commits[:250]],
        "files": [f.to_json() for f in files[:200]],
        "ignore_if_duplicate": "true",
        "pull_requests": [],
    }
    headers = {"AUTHORIZATION": f"apikey {context.root.api_key}"}
    print(f"Sending: \n{body}")
    resp = requests.post(
        f"{context.root.baseurl}/api/1/deployments/{context.organization}/{context.deployment}/register_deploy",
        json=body,
        headers=headers,
    )
    if resp.status_code == 401:
        print(f" Response: {resp.text}")
        raise ValueError("Unable to authenticate to Sleuth")
    elif resp.status_code != 200:
        raise ValueError(f"Unexpected response: {resp.text}")

    print("Deployment registered!")

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from typing import List
from typing import Set

import requests
from git import Actor
from git import Commit
from git import Diff
from git import Repo


@dataclass
class RemoteUser:
    name: str
    email: str

    def to_json(self):
        return {"name": self.name, "email": self.email}


class RemoteCommit:
    def __init__(self, url_pattern: str, source: Commit):
        self.revision: str = source.hexsha
        self.message: str = source.message
        author: Actor = source.author
        self.author = RemoteUser(author.name, author.email)
        self.date: datetime = source.committed_datetime
        self.files: Set[str] = set()
        self.parents: Set[str] = set(p.hexsha for p in source.iter_parents())
        self.url = url_pattern.replace("REVISION", self.revision)

    def to_json(self):
        return {
            "revision": self.revision,
            "message": self.message,
            "author": self.author.to_json(),
            "date": self.date.isoformat(),
            "files": list(self.files),
            "parents": list(self.parents),
            "url": self.url,
        }


class RemoteFile:
    def __init__(self, file_url_pattern: str, revision: str, path: str):
        self.path = path
        self.url = file_url_pattern.replace("REVISION", revision).replace("PATH", path)
        self.additions = 0
        self.deletions = 0

    def to_json(self):
        return {
            "path": self.path,
            "url": self.url,
            "additions": self.additions,
            "deletions": self.deletions,
        }


def get_latest_revision(
    url: str, token: str, org: str, deployment: str, environment: str
):
    query = f"""
{{
    deployment(orgSlug:"{org}", deploymentSlug:"{deployment}") {{
        ... on CodeChangeSource {{
            latestChange(environmentSlug:"{environment}") {{
                revision
            }}
        }}
    }}
}}            
    """
    headers = {"AUTHORIZATION": f"apikey {token}"}
    resp = requests.get(f"{url}/graphql", json=dict(query=query), headers=headers)
    if resp.status_code != 200:
        raise ValueError("Unable to authenticate to Sleuth")

    body = resp.json()
    if body.get("errors"):
        raise ValueError("Errors retrieving latest deployment: {body['errors']")

    return resp.json()["data"]["deployment"]["latestChange"]["revision"]


def list_paths(root_tree, path=Path(".")):
    for blob in root_tree.blobs:
        yield path / blob.name
    for tree in root_tree.trees:
        yield from list_paths(tree, path / tree.name)


def get_commit_list(
    args, head_commit: Commit, latest_commit: Commit, repo: Repo
) -> List[RemoteCommit]:
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


def get_files_list(
    args, head_commit: Commit, latest_commit: Commit
) -> List[RemoteFile]:
    diff_list = head_commit.diff(latest_commit.hexsha)
    return [
        RemoteFile(args.file_url_pattern, path=name, revision=head_commit.hexsha)
        for name in _get_files_in_diff_list(diff_list)
    ]


def send_deployment(
    args, head_commit: Commit, commits: List[RemoteCommit], files: List[RemoteFile]
):
    body = {
        "sha": head_commit.hexsha,
        "environment": args.environment,
        "date": datetime.utcnow().isoformat(),
        "commits": [c.to_json() for c in commits],
        "files": [f.to_json() for f in files],
        "pull_requests": [],
    }
    headers = {"AUTHORIZATION": f"apikey {args.token}"}
    print(f"Sending: \n{body}")
    resp = requests.post(
        f"{args.baseurl}/api/1/deployments/{args.org}/{args.deployment}/register_deploy",
        json=body,
        headers=headers,
    )
    if resp.status_code > 299:
        print(f" Response: {resp.text}")
        raise ValueError("Unable to authenticate to Sleuth")
    print("Deployment registered!")


def main():
    parser = argparse.ArgumentParser(description="Submit a deploy to Sleuth.")
    parser.add_argument(
        "-k", "--api-key", dest="token", required=True, help="the Sleuth API key"
    )
    parser.add_argument(
        "-o", "--org", dest="org", required=True, help="the Sleuth organization slug"
    )
    parser.add_argument(
        "-d",
        "--deployment",
        dest="deployment",
        required=True,
        help="the Sleuth deployment slug",
    )
    parser.add_argument(
        "--commit-url-pattern",
        dest="commit_url_pattern",
        required=True,
        help="the commit URL pattern to use for linking",
    )
    parser.add_argument(
        "--file-url-pattern",
        dest="file_url_pattern",
        required=True,
        help="the file URL pattern to use for linking",
    )
    parser.add_argument(
        "-e",
        "--environment",
        dest="environment",
        default="production",
        help="the Sleuth environment slug",
    )
    parser.add_argument(
        "--baseurl",
        type=str,
        default="https://app.sleuth.io",
        help="the base Sleuth URL",
    )
    parser.add_argument("path", nargs="?", help="the path to the git repository")

    args = parser.parse_args()

    latest_revision = get_latest_revision(
        args.baseurl, args.token, args.org, args.deployment, args.environment
    )
    repo = Repo(args.path)
    latest_commit = repo.commit(latest_revision)
    head_commit = repo.commit()
    commits = get_commit_list(args, head_commit, latest_commit, repo)
    files = get_files_list(args, head_commit, latest_commit)

    send_deployment(args, head_commit, commits, files)


if __name__ == "__main__":
    main()

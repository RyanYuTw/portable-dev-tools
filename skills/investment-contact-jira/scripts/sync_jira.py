#!/usr/bin/env python3
"""Idempotent Jira Cloud REST API sync for generated implementation tasks."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


LABELS = ["投資接洽", "自動建立"]


def load_env_file(path: Path) -> None:
    """Load simple KEY=value entries without printing secret values."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_plan(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("plan must be a JSON array of task objects")
    for item in payload:
        if not item.get("summary") or not item.get("description"):
            raise ValueError("every task needs summary and description")
    return payload


class JiraClient:
    def __init__(self) -> None:
        base_url = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
        email = os.environ.get("JIRA_EMAIL", "")
        token = os.environ.get("JIRA_API_TOKEN", "")
        if not base_url or not email or not token:
            raise RuntimeError("set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN")
        credential = base64.b64encode(f"{email}:{token}".encode()).decode()
        self.base_url = base_url
        self.auth = f"Basic {credential}"

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self.auth,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise RuntimeError(f"Jira API {error.code}: {detail[:500]}") from error

    def existing(self, project_key: str) -> dict[str, dict[str, Any]]:
        result = self.request(
            "POST",
            "/rest/api/3/search/jql",
            {
                "jql": (
                    f'project = "{project_key}" '
                    'AND labels in ("投資接洽", "investment-contact")'
                ),
                "maxResults": 100,
                "fields": ["summary", "status", "labels"],
            },
        )
        return {issue["fields"]["summary"]: issue for issue in result.get("issues", [])}

    def create(self, project_key: str, task: dict[str, Any]) -> dict[str, Any]:
        return self.request(
            "POST",
            "/rest/api/3/issue",
            {
                "fields": {
                    "project": {"key": project_key},
                    "issuetype": {"name": "Task"},
                    "summary": task["summary"],
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": task["description"]}],
                        }],
                    },
                    "labels": LABELS,
                },
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--project")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--apply", action="store_true", help="create missing issues")
    args = parser.parse_args()

    load_env_file(args.env_file)
    tasks = read_plan(args.plan)
    project_key = args.project or os.environ.get("JIRA_PROJECT_KEY")
    if not project_key:
        raise RuntimeError("set JIRA_PROJECT_KEY or pass --project")
    print(f"project={project_key} tasks={len(tasks)} mode={'apply' if args.apply else 'dry-run'}")
    if not args.apply:
        for task in tasks:
            print(f"CREATE {task['summary']}")
        return 0

    client = JiraClient()
    existing = client.existing(project_key)
    created = 0
    skipped = 0
    for task in tasks:
        if task["summary"] in existing:
            issue = existing[task["summary"]]
            print(f"SKIP {issue['key']} {task['summary']}")
            skipped += 1
            continue
        issue = client.create(project_key, task)
        print(f"CREATE {issue['key']} {task['summary']}")
        created += 1
    print(f"created={created} skipped={skipped} total={len(tasks)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)

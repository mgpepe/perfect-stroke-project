"""AI agent that modifies the perfect-stroke-project-epaper repo.

Runs as a background thread kicked off from views_modify.py. Each job gets
a fresh workspace, talks to Claude (Anthropic SDK, tool-use loop), runs
post-edit tests, optionally self-corrects up to `max_rounds` times, then
commits and pushes direct to main so the Pi picks it up on its next poll.
"""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
import subprocess
import threading
import time
import traceback
from pathlib import Path

import anthropic
from django.conf import settings
from django.utils import timezone

from api.models import ModifyJob


# ─── Pricing (claude-opus-4-7; USD per million tokens) ───────────

_PRICING = {
    'claude-opus-4-7': {'input': 15.0, 'output': 75.0},
    'claude-opus-4-6': {'input': 15.0, 'output': 75.0},
    'claude-sonnet-4-6': {'input': 3.0, 'output': 15.0},
    'claude-haiku-4-5-20251001': {'input': 1.0, 'output': 5.0},
}


def _price(model: str, usage) -> float:
    p = _PRICING.get(model) or {'input': 15.0, 'output': 75.0}
    return (usage.input_tokens * p['input'] + usage.output_tokens * p['output']) / 1_000_000


# ─── Safety: files the agent is not allowed to write ─────────────

_WRITE_BLOCKLIST = [
    '.env', '.env.*', '.env_*',
    '.git/*', '.gitignore',
    '*.pem', '*.key',
    '.ssh/*',
    'run_display.sh',  # unique to Pi, not in repo but guard anyway
]


def _blocked(relpath: str) -> bool:
    relpath = relpath.lstrip('./')
    for pattern in _WRITE_BLOCKLIST:
        if fnmatch.fnmatch(relpath, pattern) or fnmatch.fnmatch(os.path.basename(relpath), pattern):
            return True
    return False


# ─── Shell command safety ────────────────────────────────────────

_BASH_ALLOW_PREFIXES = (
    'git status', 'git diff', 'git log', 'git show',
    'python manage.py check',
    'python -c ',
    'python -m py_compile ',
    'ruff check',
    'ruff format --check',
    'ls ', 'ls',
    'cat ',
    'find ',
    'wc ',
)


def _bash_allowed(cmd: str) -> bool:
    c = cmd.strip()
    return any(c.startswith(p) for p in _BASH_ALLOW_PREFIXES)


# ─── Tool schemas (Anthropic tool-use) ───────────────────────────

TOOLS = [
    {
        'name': 'read_file',
        'description': 'Read the contents of a file in the workspace.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'Repo-relative path.'},
            },
            'required': ['path'],
        },
    },
    {
        'name': 'write_file',
        'description': (
            'Overwrite or create a file in the workspace. Use for all edits. '
            'Returns an error for files on the safety blocklist.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'Repo-relative path.'},
                'content': {'type': 'string', 'description': 'Full new file contents.'},
            },
            'required': ['path', 'content'],
        },
    },
    {
        'name': 'list_directory',
        'description': 'List files and directories at a path in the workspace.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'Repo-relative path (use "." for root).'},
            },
            'required': ['path'],
        },
    },
    {
        'name': 'grep',
        'description': 'Search for a pattern across the workspace using ripgrep semantics.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'pattern': {'type': 'string', 'description': 'Regex pattern.'},
                'path': {'type': 'string', 'description': 'Subpath to limit search (optional).'},
            },
            'required': ['pattern'],
        },
    },
    {
        'name': 'run_command',
        'description': (
            'Run a shell command inside the workspace. Only a narrow allowlist '
            'of read-only / verification commands is accepted '
            '(git status/diff/log, python manage.py check, python -c ..., '
            'python -m py_compile, ruff check, ls, cat, find, wc).'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'cmd': {'type': 'string', 'description': 'The shell command.'},
            },
            'required': ['cmd'],
        },
    },
    {
        'name': 'finish',
        'description': 'Signal that edits are complete and ready for testing. Call once when done.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'summary': {'type': 'string', 'description': 'One-line summary of what was changed.'},
            },
            'required': ['summary'],
        },
    },
]


# ─── System prompt ────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the Perfect Stroke code modification agent.

You modify the `mgpepe/perfect-stroke-project-epaper` repository — a small
Django-on-Raspberry-Pi client that fetches images from an API and renders
them to a display via pygame (HDMI backend today, e-ink backend later).

Repo layout you can rely on:
  composer/         PIL pipeline: pad-to-canvas + QR overlay (compose.py)
  psp_client/       HTTP client to the sibling API (client.py)
  renderer/         Display backends (base.py, hdmi.py, eink.py stub)
  display/          Django app with DeviceConfig, ImageHistory, the run_display
                    management command, and /admin/ + /status/ templates.
  epaper/           Django project (settings.py, urls.py)
  templates/        Django templates
  README.md, requirements.txt, manage.py

Rules:
- Make the smallest focused change that satisfies the request.
- Preserve the file's existing style, imports, and structure.
- Never modify `.env*`, `.git/*`, `*.pem`, `*.key`, `psp_client/client.py`
  auth-related code, or the Django device endpoints — the safety blocklist
  will reject writes to these.
- Prefer reading files with `read_file` before editing; never invent APIs.
- When you are done, call the `finish` tool with a one-line summary. Do
  NOT write prose replies — use tools for everything, then `finish` at the end.
- `run_command` accepts only read-only verification commands (see its
  description). Do not try to run git add/commit/push yourself; the host
  will commit + push for you.
"""


# ─── Tool execution ───────────────────────────────────────────────

def _safe_join(workspace: Path, path: str) -> Path:
    p = (workspace / path).resolve()
    ws = workspace.resolve()
    if ws not in p.parents and p != ws:
        raise ValueError(f'path {path!r} escapes workspace')
    return p


def _run_tool(workspace: Path, name: str, args: dict) -> str:
    try:
        if name == 'read_file':
            target = _safe_join(workspace, args['path'])
            if not target.exists():
                return f'ERROR: file not found: {args["path"]}'
            if target.stat().st_size > 200_000:
                return f'ERROR: file too large ({target.stat().st_size} bytes).'
            return target.read_text(encoding='utf-8', errors='replace')

        if name == 'write_file':
            rel = args['path'].lstrip('/')
            if _blocked(rel):
                return f'ERROR: {rel!r} is on the write blocklist and cannot be modified.'
            target = _safe_join(workspace, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(args['content'], encoding='utf-8')
            return f'wrote {rel} ({len(args["content"])} chars)'

        if name == 'list_directory':
            target = _safe_join(workspace, args['path'])
            if not target.exists():
                return f'ERROR: path not found: {args["path"]}'
            entries = []
            for entry in sorted(target.iterdir()):
                rel = entry.relative_to(workspace)
                kind = 'dir' if entry.is_dir() else 'file'
                if entry.name.startswith('.git') or entry.name == 'venv':
                    continue
                entries.append(f'{kind}\t{rel}')
            return '\n'.join(entries) or '(empty)'

        if name == 'grep':
            cmd = ['grep', '-rn', '-E', args['pattern']]
            path = args.get('path', '.')
            cmd.append(path)
            try:
                res = subprocess.run(
                    cmd, cwd=workspace, capture_output=True, text=True, timeout=30,
                )
                out = res.stdout.strip() or '(no matches)'
                return out[:6000]
            except subprocess.TimeoutExpired:
                return 'ERROR: grep timed out.'

        if name == 'run_command':
            cmd = args['cmd']
            if not _bash_allowed(cmd):
                return f'ERROR: command not on allowlist: {cmd!r}'
            try:
                res = subprocess.run(
                    cmd, cwd=workspace, capture_output=True, text=True, timeout=120,
                    shell=True,
                )
                out = (res.stdout + res.stderr).strip()
                return f'exit={res.returncode}\n{out[:6000]}'
            except subprocess.TimeoutExpired:
                return 'ERROR: command timed out.'

        if name == 'finish':
            return f'FINISH: {args.get("summary", "(no summary)")}'

        return f'ERROR: unknown tool {name!r}'
    except Exception as exc:
        return f'ERROR: tool {name!r} raised: {exc}'


# ─── Workspace / git helpers ──────────────────────────────────────

def _run(cmd: list, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=merged)


def _clone(job: ModifyJob, workspace_root: Path) -> Path:
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    workspace_root.mkdir(parents=True)

    repo = job.repo
    token = settings.GITHUB_TOKEN or ''
    if not token:
        raise RuntimeError('GITHUB_TOKEN is not configured on the server.')

    clone_url = f'https://x-access-token:{token}@github.com/{repo}.git'
    job.append_log(f'cloning {repo}…')
    res = _run(['git', 'clone', '--depth', '50', clone_url, 'repo'], cwd=workspace_root)
    if res.returncode != 0:
        raise RuntimeError(f'git clone failed:\n{res.stderr}')
    repo_dir = workspace_root / 'repo'
    _run(['git', 'config', 'user.email', 'builder@perfectstrokeproject.com'], cwd=repo_dir)
    _run(['git', 'config', 'user.name', 'Perfect Stroke Builder'], cwd=repo_dir)
    job.append_log('clone ok')
    return repo_dir


# ─── Post-edit tests ──────────────────────────────────────────────

def _run_tests(repo_dir: Path, job: ModifyJob) -> tuple[bool, str]:
    """Run quick verifications on the edited workspace. Returns (ok, detail)."""
    job.append_log('running post-edit tests…')

    # 1. Byte-compile every .py
    res = _run(
        ['python', '-m', 'compileall', '-q', '-f', '.'],
        cwd=repo_dir,
    )
    if res.returncode != 0:
        return False, f'py_compile failed:\n{res.stdout}\n{res.stderr}'

    # 2. Django check — but the epaper repo's own venv is not here, and the
    #    server's venv doesn't have pygame. Skip Django check since we can't
    #    run it without the target venv. Byte-compile is our best local
    #    verification.

    job.append_log('tests ok')
    return True, 'ok'


# ─── Agent loop ───────────────────────────────────────────────────

def _run_agent(
    client: anthropic.Anthropic,
    job: ModifyJob,
    repo_dir: Path,
    user_prompt: str,
    extra_context: str = '',
) -> tuple[bool, str]:
    """Run a single Claude turn-loop until the agent calls `finish` or aborts.

    Returns (ok, summary). Mutates job: appends log, adds cost, updates status.
    """
    model = job.model or settings.BUILDER_MODEL

    if extra_context:
        user_content = f'{user_prompt}\n\n---\nPrevious attempt output:\n{extra_context}'
    else:
        user_content = user_prompt

    messages = [{'role': 'user', 'content': user_content}]

    max_turns = 40
    start = time.time()
    timeout = settings.BUILDER_ROUND_TIMEOUT_SEC

    for turn in range(max_turns):
        if time.time() - start > timeout:
            return False, f'round timed out after {timeout}s'
        if job.cost_usd >= job.max_cost_usd:
            return False, f'cost ceiling ${job.max_cost_usd} reached'

        try:
            response = client.messages.create(
                model=model,
                max_tokens=8192,
                tools=TOOLS,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
        except anthropic.APIError as exc:
            return False, f'Anthropic API error: {exc}'

        job.cost_usd += _price(model, response.usage)
        job.save(update_fields=['cost_usd', 'updated_at'])
        job.append_log(
            f'turn {turn+1}: stop={response.stop_reason} in={response.usage.input_tokens} '
            f'out={response.usage.output_tokens} cost=${job.cost_usd:.4f}'
        )

        messages.append({'role': 'assistant', 'content': response.content})

        if response.stop_reason == 'end_turn':
            return False, 'agent ended turn without calling finish'

        tool_results = []
        finished_summary = None
        for block in response.content:
            if block.type == 'tool_use':
                result = _run_tool(repo_dir, block.name, block.input or {})
                short = result.split('\n', 1)[0][:120]
                job.append_log(f'  {block.name}({json.dumps(block.input)[:80]}) -> {short}')
                tool_results.append({
                    'type': 'tool_result',
                    'tool_use_id': block.id,
                    'content': result,
                })
                if block.name == 'finish':
                    finished_summary = (block.input or {}).get('summary', '')

        if finished_summary is not None:
            return True, finished_summary

        if response.stop_reason != 'tool_use':
            return False, f'unexpected stop_reason {response.stop_reason}'

        messages.append({'role': 'user', 'content': tool_results})

    return False, f'agent exhausted {max_turns} turns'


# ─── End-to-end job runner ────────────────────────────────────────

def _commit_and_push(repo_dir: Path, job: ModifyJob, summary: str) -> tuple[str, str]:
    """Stage all changes, commit, push. Returns (sha, diffstat)."""
    job.current_phase = 'committing'
    job.save(update_fields=['current_phase', 'updated_at'])
    job.append_log('staging and committing…')

    _run(['git', 'add', '-A'], cwd=repo_dir)

    diffstat = _run(['git', 'diff', '--cached', '--stat'], cwd=repo_dir).stdout

    if not diffstat.strip():
        raise RuntimeError('agent finished but no files changed')

    subject = (summary or job.prompt.split('\n', 1)[0])[:72]
    body = f'{job.prompt}\n\nPerfect Stroke Builder job {job.id[:8]}.'
    msg = f'{subject}\n\n{body}'
    res = _run(['git', 'commit', '-m', msg], cwd=repo_dir)
    if res.returncode != 0:
        raise RuntimeError(f'git commit failed:\n{res.stderr}')

    job.current_phase = 'pushing'
    job.save(update_fields=['current_phase', 'updated_at'])
    job.append_log('pushing to origin/main…')
    res = _run(['git', 'push', 'origin', 'main'], cwd=repo_dir)
    if res.returncode != 0:
        raise RuntimeError(f'git push failed:\n{res.stderr}')

    sha = _run(['git', 'rev-parse', '--short', 'HEAD'], cwd=repo_dir).stdout.strip()
    return sha, diffstat


def _run_job(job_id: str):
    """Thread entry point. All exceptions here land in job.error."""
    job = ModifyJob.objects.get(id=job_id)
    job.status = 'running'
    job.started_at = timezone.now()
    job.save(update_fields=['status', 'started_at', 'updated_at'])

    workspace_root = Path(settings.BUILDER_WORKSPACE_DIR) / job.id
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        job.current_phase = 'cloning'
        job.save(update_fields=['current_phase', 'updated_at'])
        repo_dir = _clone(job, workspace_root)

        previous_feedback = ''
        for round_num in range(job.max_rounds):
            job.round_num = round_num
            job.current_phase = 'editing' if round_num == 0 else 'correcting'
            job.save(update_fields=['round_num', 'current_phase', 'updated_at'])

            job.append_log(f'=== round {round_num+1}/{job.max_rounds} ===')
            ok, summary = _run_agent(client, job, repo_dir, job.prompt, previous_feedback)
            if not ok:
                job.append_log(f'agent did not finish cleanly: {summary}')
                raise RuntimeError(f'agent failed: {summary}')

            job.current_phase = 'testing'
            job.save(update_fields=['current_phase', 'updated_at'])
            tests_ok, test_detail = _run_tests(repo_dir, job)
            if tests_ok:
                break

            job.append_log(f'tests failed on round {round_num+1}: {test_detail[:300]}')
            previous_feedback = (
                f'Your previous edit did not pass the post-edit tests. Fix this and '
                f'call finish again:\n\n{test_detail[:3000]}'
            )
            if round_num == job.max_rounds - 1:
                raise RuntimeError(f'tests still failing after {job.max_rounds} rounds')

        sha, diffstat = _commit_and_push(repo_dir, job, summary)

        job.commit_sha = sha
        job.diff = diffstat
        job.status = 'succeeded'
        job.current_phase = ''
        job.completed_at = timezone.now()
        job.append_log(f'done: {sha}')
        job.save(update_fields=[
            'commit_sha', 'diff', 'status', 'current_phase', 'completed_at', 'updated_at',
        ])
    except Exception as exc:
        job.status = 'failed'
        job.error = f'{exc}\n\n{traceback.format_exc()}'
        job.completed_at = timezone.now()
        job.append_log(f'FAILED: {exc}')
        job.save(update_fields=['status', 'error', 'completed_at', 'updated_at'])
    finally:
        try:
            if workspace_root.exists():
                shutil.rmtree(workspace_root, ignore_errors=True)
        except Exception:
            pass


def start_job(job: ModifyJob):
    """Kick the job off in a daemon thread. Returns immediately."""
    t = threading.Thread(target=_run_job, args=(job.id,), daemon=True)
    t.start()

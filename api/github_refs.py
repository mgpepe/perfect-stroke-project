"""Fetch refs (commits, branches, tags) from GitHub for the version picker.

Cached for 60 s so paging through the panel doesn't hammer the GitHub API.
Missing token or any API error returns an empty result — the UI degrades
gracefully to just the free-text field.
"""

import logging

import requests
from django.conf import settings
from django.core.cache import cache

log = logging.getLogger(__name__)


_API = 'https://api.github.com'
_HEADERS_BASE = {
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
}
_TIMEOUT = 5.0
_TTL = 60


def _headers():
    token = getattr(settings, 'GITHUB_TOKEN', '') or ''
    if not token:
        return None
    return {**_HEADERS_BASE, 'Authorization': f'Bearer {token}'}


def _repo():
    return getattr(settings, 'GITHUB_REPO', '') or ''


def _get(path, params=None):
    headers = _headers()
    if headers is None:
        return None
    url = f'{_API}{path}'
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=_TIMEOUT)
        if resp.status_code != 200:
            log.warning('GitHub %s -> %d: %s', url, resp.status_code, resp.text[:200])
            return None
        return resp.json()
    except requests.RequestException as exc:
        log.warning('GitHub %s failed: %s', url, exc)
        return None


def recent_commits(limit=20):
    """List of {sha, short_sha, subject, author, date} for the panel dropdown."""
    repo = _repo()
    if not repo:
        return []
    cache_key = f'gh:commits:{repo}:{limit}'
    hit = cache.get(cache_key)
    if hit is not None:
        return hit
    data = _get(f'/repos/{repo}/commits', params={'per_page': limit})
    if not data:
        cache.set(cache_key, [], 10)
        return []
    out = []
    for c in data:
        msg = (c.get('commit', {}).get('message') or '').split('\n', 1)[0]
        sha = c.get('sha') or ''
        out.append({
            'sha': sha,
            'short_sha': sha[:7],
            'subject': msg,
            'author': (c.get('commit', {}).get('author') or {}).get('name') or '',
            'date': (c.get('commit', {}).get('author') or {}).get('date') or '',
        })
    cache.set(cache_key, out, _TTL)
    return out


def branches():
    repo = _repo()
    if not repo:
        return []
    cache_key = f'gh:branches:{repo}'
    hit = cache.get(cache_key)
    if hit is not None:
        return hit
    data = _get(f'/repos/{repo}/branches', params={'per_page': 50})
    out = [{'name': b['name'], 'sha': (b.get('commit') or {}).get('sha', '')} for b in (data or [])]
    cache.set(cache_key, out, _TTL)
    return out


def tags():
    repo = _repo()
    if not repo:
        return []
    cache_key = f'gh:tags:{repo}'
    hit = cache.get(cache_key)
    if hit is not None:
        return hit
    data = _get(f'/repos/{repo}/tags', params={'per_page': 30})
    out = [{'name': t['name'], 'sha': (t.get('commit') or {}).get('sha', '')} for t in (data or [])]
    cache.set(cache_key, out, _TTL)
    return out


def commit_info(ref):
    """Resolve a branch/tag/sha to {sha, short_sha, subject, author, date}."""
    repo = _repo()
    if not repo or not ref:
        return None
    cache_key = f'gh:commit:{repo}:{ref}'
    hit = cache.get(cache_key)
    if hit is not None:
        return hit
    data = _get(f'/repos/{repo}/commits/{ref}')
    if not data:
        cache.set(cache_key, {}, 10)
        return None
    sha = data.get('sha') or ''
    msg = (data.get('commit', {}).get('message') or '').split('\n', 1)[0]
    out = {
        'sha': sha,
        'short_sha': sha[:7],
        'subject': msg,
        'author': (data.get('commit', {}).get('author') or {}).get('name') or '',
        'date': (data.get('commit', {}).get('author') or {}).get('date') or '',
    }
    cache.set(cache_key, out, _TTL)
    return out


def enabled():
    return bool(_headers()) and bool(_repo())

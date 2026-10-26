"""Deliberately wrong reproducer: uses transport URL as the target base."""

from urllib.parse import urljoin


def naive_next_target(response_url, href):
    return urljoin(response_url, href)

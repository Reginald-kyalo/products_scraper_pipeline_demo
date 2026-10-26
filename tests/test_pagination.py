from urllib.parse import parse_qs, urlsplit

import pytest
from pagination import next_target, unwrap_target, wrap_target


def test_relative_next_uses_catalogue_not_proxy_wrapper():
    # A join against the transport URL silently drops /catalogue/.
    response_url = (
        "https://proxy.example/?url=https%3A%2F%2Fbooks.toscrape.com%2Fcatalogue%2Fpage-1.html"
    )
    assert next_target(response_url, "page-2.html") == (
        "https://books.toscrape.com/catalogue/page-2.html"
    )


def test_unwrap_nested_urls_preserves_encoded_target_query():
    target = "https://books.toscrape.com/catalogue/page-2.html?q=a%26b&page=2"
    assert unwrap_target(wrap_target(wrap_target(target))) == target


def test_plain_target_with_url_parameter_is_not_a_wrapper():
    target = "https://books.toscrape.com/?url=https://example.org/"
    assert unwrap_target(target) == target


@pytest.mark.parametrize(
    "target",
    [
        "file:///etc/example",
        "javascript:alert(1)",
        "//books.toscrape.com/",
        "https://user:pass@books.toscrape.com/",
    ],
)
def test_rejects_non_http_and_embedded_credentials(target):
    with pytest.raises(ValueError):
        wrap_target(target)


@pytest.mark.parametrize(
    "wrapper",
    [
        "https://proxy.example/",
        "https://proxy.example/?url=",
        "https://proxy.example/?url=https://example.org/&url=https://example.net/",
    ],
)
def test_rejects_ambiguous_wrappers(wrapper):
    with pytest.raises(ValueError):
        unwrap_target(wrapper)


def test_prevents_cross_origin_next_link():
    with pytest.raises(ValueError):
        next_target("https://books.toscrape.com/catalogue/page-1.html", "//example.net/")


def test_transport_wraps_exactly_once():
    value = wrap_target(wrap_target("https://books.toscrape.com/catalogue/page-2.html"))
    assert parse_qs(urlsplit(value).query)["url"] == [
        "https://books.toscrape.com/catalogue/page-2.html"
    ]


@pytest.mark.xfail(strict=True, reason="Reproducer joins against proxy transport origin")
def test_broken_reproducer():
    from broken_example import naive_next_target

    assert (
        naive_next_target(
            "https://proxy.example/?url=https%3A%2F%2Fbooks.toscrape.com%2Fcatalogue%2Fpage-1.html",
            "page-2.html",
        )
        == "https://books.toscrape.com/catalogue/page-2.html"
    )


@pytest.mark.parametrize(
    "target",
    [
        "https://books.toscrape.com:not-a-port/page",
        "https://books.toscrape.com:99999/page",
        "https://books.toscrape.com/\npage",
        "https://books.toscrape.com/with space",
    ],
)
def test_malformed_ports_and_literal_controls_not_wrapped(target):
    with pytest.raises(ValueError):
        wrap_target(target)

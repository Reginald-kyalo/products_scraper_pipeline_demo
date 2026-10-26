"""Keep target pagination separate from the proxy API's transport URL."""

from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

WRAPPER = "https://proxy.example/"


def _validate(url: str) -> str:
    if any(ord(character) <= 32 or ord(character) == 127 for character in url):
        raise ValueError("URL spaces and control characters must be encoded")
    parsed = urlsplit(url)
    # urlsplit delays port validation until this property is accessed.
    _ = parsed.port
    if (
        parsed.scheme not in {"https", "http"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError("Expected an absolute HTTP(S) URL without embedded credentials")
    return url


def unwrap_target(url: str) -> str:
    """Decode only the known wrapper; query decoding happens once per layer."""
    for _ in range(8):
        _validate(url)
        parsed = urlsplit(url)
        if (parsed.scheme, parsed.netloc, parsed.path) != ("https", "proxy.example", "/"):
            return url
        values = parse_qs(parsed.query, keep_blank_values=True).get("url", [])
        if len(values) != 1 or not values[0]:
            raise ValueError("Wrapper must contain exactly one nonempty target")
        url = values[0]
    raise ValueError("Too many nested wrappers")


def wrap_target(url: str) -> str:
    return WRAPPER + "?" + urlencode({"url": unwrap_target(url)})


def next_target(response_url: str, href: str) -> str:
    base = unwrap_target(response_url)
    target = _validate(urljoin(base, href))
    if urlsplit(target).netloc != urlsplit(base).netloc:
        raise ValueError("Pagination must stay on the target origin")
    if urlsplit(target).scheme != urlsplit(base).scheme:
        raise ValueError("Pagination must preserve the target scheme")
    return target


if __name__ == "__main__":
    start = wrap_target("https://books.toscrape.com/catalogue/page-1.html")
    print("Naive:", urljoin(start, "page-2.html"))
    print("Fixed:", next_target(start, "page-2.html"))
    print("Transport:", wrap_target(next_target(start, "page-2.html")))

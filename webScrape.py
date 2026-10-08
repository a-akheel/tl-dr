"""Bounded public-URL fetching and heuristic HTML article extraction."""
import ipaddress
import socket
import ssl
from urllib.parse import urljoin, urlsplit

import urllib3
from bs4 import BeautifulSoup

MAX_HTML_BYTES = 2 * 1024 * 1024


def public_target(url):
    try:
        parsed = urlsplit(url)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username or parsed.password or port not in {80, 443}):
            raise ValueError("Enter a public HTTP or HTTPS article URL.")
        host = parsed.hostname.encode("idna").decode("ascii")
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
            raise ValueError("Only public article URLs are supported.")
        return parsed, host, port, addresses[0][4][0]
    except (OSError, UnicodeError):
        raise ValueError("Could not resolve this article URL.") from None


def fetch_html(url):
    for _ in range(4):
        parsed, host, port, address = public_target(url)
        # Pin the validated IP, preserving the original host for TLS and HTTP.
        options = {"timeout": urllib3.Timeout(connect=5, read=10), "retries": False}
        if parsed.scheme == "https":
            pool = urllib3.HTTPSConnectionPool(address, port, server_hostname=host,
                assert_hostname=host, ssl_context=ssl.create_default_context(), **options)
        else:
            pool = urllib3.HTTPConnectionPool(address, port, **options)
        host_header = f"[{host}]" if ":" in host else host
        if port != (443 if parsed.scheme == "https" else 80):
            host_header += f":{port}"
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        response = None
        try:
            response = pool.request("GET", path, headers={"Host": host_header,
                "User-Agent": "TLDR-Portfolio-Demo/1.0", "Accept-Encoding": "identity"},
                redirect=False, preload_content=False)
            if response.status in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location")
                if not location:
                    raise ValueError("This URL has an invalid redirect.")
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise ValueError("This article is unavailable. Paste its text instead.")
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                raise ValueError("Use an HTML article URL or upload the document instead.")
            chunks = []
            length = 0
            for chunk in response.stream(16_384):
                length += len(chunk)
                if length > MAX_HTML_BYTES:
                    raise ValueError("This article page is too large. Paste its text instead.")
                chunks.append(chunk)
            return b"".join(chunks)
        except urllib3.exceptions.HTTPError:
            raise ValueError("Could not retrieve this article. Paste its text instead.") from None
        finally:
            if response is not None:
                response.close()
            pool.close()
    raise ValueError("Too many article redirects. Paste the text instead.")


def getArticle(url):
    soup = BeautifulSoup(fetch_html(url), "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for node in soup.select("script, style, nav, header, footer, aside, form"):
        node.decompose()
    article = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs = [paragraph.get_text(" ", strip=True) for paragraph in article.find_all("p")]
    text = "\n".join(paragraph for paragraph in paragraphs if paragraph)
    if not text:
        raise ValueError("No article text found. Paste the text instead.")
    return title, text

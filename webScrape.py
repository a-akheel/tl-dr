"""URL fetching is opt-in and restricted to operator-trusted HTTPS hosts."""

import os
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


def getArticle(url):
    parsed = urlparse(url)
    allowed = {
        x.strip().lower()
        for x in os.environ.get("ARTICLE_ALLOWED_HOSTS", "").split(",")
        if x.strip()
    }
    if (
        parsed.scheme != "https"
        or parsed.hostname not in allowed
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("URL host is not explicitly allowed")
    # Redirects cannot escape the configured host; proxy variables are not inherited.
    try:
        with requests.Session() as session:
            session.trust_env = False
            with session.get(
                url, timeout=(5, 15), allow_redirects=False, stream=True
            ) as response:
                if (
                    response.status_code != 200
                    or "text/html" not in response.headers.get("Content-Type", "")
                ):
                    raise ValueError("Expected an HTML response without redirects")
                body = bytearray()
                for chunk in response.iter_content(16384):
                    body.extend(chunk)
                    if len(body) > 2_000_000:
                        raise ValueError("Page too large")
        soup = BeautifulSoup(bytes(body), "html.parser")
        for element in soup(["script", "style", "nav", "footer"]):
            element.decompose()
        text = "\n".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        return soup.title.get_text(strip=True) if soup.title else "", text
    except requests.RequestException as exc:
        raise ValueError("Unable to retrieve article") from exc

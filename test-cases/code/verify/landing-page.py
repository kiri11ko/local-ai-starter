"""Hidden check for the landing-page case: the structural requirements stated in the prompt."""
import re
import sys
from html.parser import HTMLParser


class Collect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def read(name):
    try:
        return open(name, encoding="utf-8").read()
    except OSError:
        return ""


html, css, js = read("index.html"), read("styles.css"), read("script.js")
page = Collect()
page.feed(html)
tags = page.tags
has = lambda tag, **want: any(t == tag and all(v in (a.get(k) or "") for k, v in want.items()) for t, a in tags)
classes = " ".join(a.get("class") or "" for _, a in tags)
checks = {
    "index.html, styles.css and script.js exist": bool(html and css and js),
    "<title> present": has("title"),
    "viewport meta": has("meta", name="viewport"),
    "styles.css linked": has("link", href="styles.css"),
    "script.js included": has("script", src="script.js"),
    "header, main and footer": all(has(t) for t in ("header", "main", "footer")),
    "button#theme-toggle": has("button", id="theme-toggle"),
    "at least 3 .feature cards": classes.split().count("feature") >= 3,
    "pricing section #pricing": any(a.get("id") == "pricing" for _, a in tags),
    "contact form with email input": has("form") and has("input", type="email"),
    "dark theme rule [data-theme=\"dark\"]": bool(re.search(r"\[data-theme=[\"']?dark", css)),
    "media query for phones": "@media" in css,
    "toggle remembered in localStorage": "localStorage" in js,
    "respects prefers-color-scheme": "prefers-color-scheme" in css + js,
}
for name, passed in checks.items():
    print(("ok    " if passed else "FAIL  ") + name)
print(f"{sum(checks.values())} of {len(checks)} requirements met")
sys.exit(0 if all(checks.values()) else 1)

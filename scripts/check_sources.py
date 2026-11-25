"""Test access to league source pages, without changing standings or Netlify."""
import datetime
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

SOURCES = {
    "GTHL AAA": "https://gthlcanada.com/schedule/",
    "OMHA AAA East/West": "https://omha-aaa.net/Groups/1216/Schedule/",
    "Tri-County U13 AA": "https://tcmhl.ca/Groups/1447/Schedule/",
}

def inspect(name, url):
    result = {"league": name, "url": url, "http_status": None,
              "bytes": 0, "accessible": False, "error": None}
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; HockeyScheduleDiagnostic/1.0)",
                                        "Accept": "text/html"})
        with urlopen(request, timeout=25) as response:
            body = response.read(1_000_000)
            result["http_status"] = response.status
            result["bytes"] = len(body)
            text = body.decode("utf-8", errors="replace").lower()
            blocked = any(word in text for word in ("checking your browser", "just a moment", "access denied"))
            result["accessible"] = response.status == 200 and not blocked
            if blocked:
                result["error"] = "Possible anti-bot page"
    except HTTPError as exc:
        result["http_status"] = exc.code
        result["error"] = f"HTTP {exc.code}"
    except (URLError, TimeoutError, OSError) as exc:
        result["error"] = str(exc)[:180]
    return result

if __name__ == "__main__":
    now = datetime.datetime.now(ZoneInfo("America/Toronto"))
    data = {"checked_at": now.isoformat(),
            "yesterday": (now.date() - datetime.timedelta(days=1)).isoformat(),
            "scope": "SOURCE CONNECTIVITY ONLY — no score parsing or publishing",
            "sources": [inspect(name, url) for name, url in SOURCES.items()]}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/source-check.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf8")
    for item in data["sources"]:
        print(item)
    print("Note: HTTP connectivity does not establish reliable access to game scores.")

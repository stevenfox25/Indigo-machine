from __future__ import annotations

import json
import urllib.request

API = "http://127.0.0.1:8000"  # change if needed
LANE = 1


def main() -> None:
    payload = {
        "command": "lane1recipe",
        "fixedholdtime": True,
        "numberofautopinbreaks": 10,
        "autopinbreak": True,
        "autopinbreaktime": [1000] * 10,
        "autopinbreakpressure": [1.0] * 10,
        "postpinbreakthermaltemp": [22.0] * 10,
        "postpinbreakpressure": [1.0] * 10,
        "postpinbreakrefluxtemp": [1.0] * 10,
        "postpinbreakstirspeed": [500] * 10,
        "attempttime": 52200,
        "thermaltemp": -10,
        "refluxenabled": True,
        "refluxtemp": 1,
        "purgevacswitchpoint": 0,
        "stirspeed": 500,
        "purgesetpressure": 1,
        "cycletype": "full",
        "name": "Lane 1 Example",
    }

    url = f"{API}/api/lanes/{LANE}/recipe"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=5) as resp:
        body = resp.read().decode("utf-8")
        print(resp.status, body)

    # fetch it back
    url2 = f"{API}/api/lanes/{LANE}/recipe"
    with urllib.request.urlopen(url2, timeout=5) as resp2:
        body2 = resp2.read().decode("utf-8")
        print(resp2.status, body2)


if __name__ == "__main__":
    main()

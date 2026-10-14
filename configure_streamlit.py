"""
Writes the per-deployment Streamlit server settings that depend on the
domain (run by docker-entrypoint.sh before Streamlit starts).

Streamlit list options (server.corsAllowedOrigins, server.allowedHosts)
cannot be passed reliably through STREAMLIT_* environment variables, so
they are written to the user-level config file (~/.streamlit/config.toml),
which Streamlit merges with the project's .streamlit/config.toml.

    MAKU_DOMAIN=maku.ae            -> origin https://maku.ae, host maku.ae
    MAKU_EXTRA_ORIGINS=https://a,https://b   (optional, comma-separated)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    domain = os.environ.get("MAKU_DOMAIN", "").strip().lower()
    if not domain:
        print("configure_streamlit: MAKU_DOMAIN not set - leaving CORS/host settings at their defaults")
        return 0
    origins = [f"https://{domain}"]
    origins += [o.strip() for o in os.environ.get("MAKU_EXTRA_ORIGINS", "").split(",") if o.strip()]
    hosts = sorted({domain, "localhost", "127.0.0.1"} | {o.split("://", 1)[-1] for o in origins})
    target = Path.home() / ".streamlit" / "config.toml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "# Generated at container start by configure_streamlit.py - do not edit.\n"
        "[server]\n"
        f"corsAllowedOrigins = {json.dumps(origins)}\n"
        f"allowedHosts = {json.dumps(hosts)}\n",
        encoding="utf-8",
    )
    print(f"configure_streamlit: CORS origins {origins}; allowed hosts {hosts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

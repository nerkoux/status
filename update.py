import os
import re
import subprocess
import requests
from datetime import datetime, UTC

BASE = "/opt/github/status"

os.chdir(BASE)

INFO_API = "https://status.akshatmehta.com/api/status-page/aki"
HEART_API = "https://status.akshatmehta.com/api/status-page/heartbeat/aki"

info = requests.get(INFO_API, timeout=20).json()
heart = requests.get(HEART_API, timeout=20).json()

heartbeat_data = heart["heartbeatList"]

rows = []

up = 0
down = 0
unknown = 0

for group in info["publicGroupList"]:

    for mon in group["monitorList"]:

        monitor_id = str(mon["id"])
        name = mon["name"]

        hb = heartbeat_data.get(monitor_id, [])

        if hb:

            latest = hb[-1]

            status_code = latest.get("status", 0)

            ping = latest.get("ping")

            ping_display = "N/A"

            # Try Kuma heartbeat ping first
            try:

                ping_value = float(ping)

                if ping_value > 0:
                    ping_display = f"{round(ping_value, 2)}ms"

            except:
                pass

            # Fallback to direct system ping
            if ping_display == "N/A":

                hostname = None

                if mon.get("hostname"):
                    hostname = mon["hostname"]

                elif mon.get("url"):
                    hostname = mon["url"]

                if hostname:

                    try:

                        result = subprocess.check_output(
                            ["ping", "-c", "1", hostname],
                            text=True,
                            stderr=subprocess.DEVNULL
                        )

                        match = re.search(
                            r'time=([\d.]+)',
                            result
                        )

                        if match:

                            ping_value = float(match.group(1))

                            ping_display = (
                                f"{round(ping_value, 2)}ms"
                            )

                    except:
                        ping_display = "N/A"

            if status_code == 1:

                status = "🟢 Operational"

                badge = (
                    "https://img.shields.io/badge/"
                    "status-operational-brightgreen"
                )

                up += 1

            elif status_code == 0:

                status = "🔴 Offline"

                badge = (
                    "https://img.shields.io/badge/"
                    "status-offline-red"
                )

                down += 1

            else:

                status = "🟠 Unknown"

                badge = (
                    "https://img.shields.io/badge/"
                    "status-unknown-orange"
                )

                unknown += 1

        else:

            status = "⚪ No Data"

            badge = (
                "https://img.shields.io/badge/"
                "status-no--data-lightgrey"
            )

            ping_display = "N/A"

            unknown += 1

        rows.append(
            f"| {name} | {status} | {ping_display} | ![]({badge}) |"
        )

total = up + down + unknown

if down == 0 and unknown == 0:

    overall = "🟢 All Systems Operational"

    overall_badge = (
        "https://img.shields.io/badge/"
        "STATUS-ALL_SYSTEMS_OPERATIONAL-brightgreen"
        "?style=for-the-badge"
    )

elif down > 0:

    overall = "🔴 Partial Outage"

    overall_badge = (
        "https://img.shields.io/badge/"
        "STATUS-PARTIAL_OUTAGE-red"
        "?style=for-the-badge"
    )

else:

    overall = "🟠 Degraded"

    overall_badge = (
        "https://img.shields.io/badge/"
        "STATUS-DEGRADED-orange"
        "?style=for-the-badge"
    )

content = f"""
# Akshat Network Infrastructure

<div align="center">

![]({overall_badge})

### Real-Time Homelab Infrastructure Monitoring

Self-hosted monitoring dashboard for infrastructure, services, networking, databases, and internal applications.

---

![Operational](https://img.shields.io/badge/Operational-{up}-brightgreen?style=flat-square)
![Offline](https://img.shields.io/badge/Offline-{down}-red?style=flat-square)
![Unknown](https://img.shields.io/badge/Unknown-{unknown}-orange?style=flat-square)
![Total](https://img.shields.io/badge/Total_Monitors-{total}-blue?style=flat-square)

</div>

---

## Current Infrastructure Status

{overall}

_Last Updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_

| Service | Status | Response Time | Badge |
|---|---|---|---|
{chr(10).join(rows)}

---

## Infrastructure Overview

    Monitoring Stack
    ├── Uptime Kuma
    ├── GitHub Auto Sync
    ├── Python Automation
    ├── Cron Scheduler
    └── Self-Hosted Infrastructure

---

## Live Status Page

- https://status.akshatmehta.com

---

## Repository Automation

This repository updates automatically every 5 minutes using a self-hosted infrastructure automation container.

---

<div align="center">

Developed by Akshat Mehta

</div>
"""

with open("README.md", "w") as f:
    f.write(content)

subprocess.run(["git", "add", "README.md"])

result = subprocess.run(
    ["git", "status", "--porcelain"],
    capture_output=True,
    text=True
)

if result.stdout.strip():

    subprocess.run([
        "git",
        "commit",
        "-m",
        "automatic status update"
    ])

    subprocess.run(["git", "push"])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Temporary TSUN Local diagnostic for GEN4/1097 logger TCP behavior.
No factory reset. No Wi-Fi/cloud/UART/inverter register changes.

The hidden page is observation-only. If unavailable, the test continues.
Default target: 192.168.1.176
Test flow: 8899 -> store 8898 -> restart -> verify -> store 8899 -> restart -> verify.
If 8898 is already stored or active, resume mode offers direct restore to 8899.
"""

import argparse
import base64
import datetime as dt
import getpass
import os
import platform
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_HOST = "192.168.1.176"
PORT_ORIGINAL = 8899
PORT_TEST = 8898
SETTING_PAGE = "/hide_set_edit.html"
COMMAND_PAGE = "/do_cmd.html"
RESTART_PAGE = "/success.html"


class Reporter:
    def __init__(self):
        self.lines = []

    def log(self, msg=""):
        print(msg)
        self.lines.append(str(msg))

    def save(self):
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.abspath(f"tsun_1097_port_restart_test_{stamp}.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self.lines) + "\n")
        return path


def confirm(msg):
    while True:
        answer = input(f"\n{msg} [y/N] ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("", "n", "no"):
            return False
        print("Please answer y or n.")


def basic_auth(user, password):
    raw = f"{user}:{password}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def headers(user=None, password=None, referer=None):
    h = {"User-Agent": "TSUN-1097-Port-Test/1.0", "Accept": "*/*"}
    if referer:
        h["Referer"] = referer
    if user is not None:
        h["Authorization"] = basic_auth(user, password or "")
    return h


def raw_request(url, method="GET", data=None, hdrs=None, timeout=6):
    req = urllib.request.Request(url, method=method, data=data, headers=hdrs or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def credentials():
    print("\nThe logger requires HTTP authentication.")
    print("Standard credentials are usually:")
    print("  Username: admin")
    print("  Password: admin")
    user = input("Logger username [admin]: ").strip() or "admin"
    pwd = getpass.getpass("Logger password [admin]: ") or "admin"
    return user, pwd


def request(url, method="GET", data=None, user=None, password=None, referer=None, timeout=6):
    h = headers(user, password, referer)
    if data is not None:
        h["Content-Type"] = "application/x-www-form-urlencoded"
    try:
        status, body = raw_request(url, method, data, h, timeout)
        return status, body, user, password
    except urllib.error.HTTPError as err:
        if err.code != 401 or user is not None:
            raise
    user, password = credentials()
    h = headers(user, password, referer)
    if data is not None:
        h["Content-Type"] = "application/x-www-form-urlencoded"
    status, body = raw_request(url, method, data, h, timeout)
    return status, body, user, password


def tcp_open(host, port, timeout=2):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def extract(html, name):
    for pattern in (
        rf'var\s+{re.escape(name)}\s*=\s*"([^"]*)"',
        rf"var\s+{re.escape(name)}\s*=\s*'([^']*)'",
    ):
        m = re.search(pattern, html)
        if m:
            return m.group(1)
    return None


def read_hide(host, user, password):
    if not tcp_open(host, 80):
        return {"available": False, "config": None, "detail": "HTTP port 80 closed"}, user, password
    try:
        status, html, user, password = request(
            f"http://{host}{SETTING_PAGE}", user=user, password=password
        )
        cfg = {
            "protocol": extract(html, "net_setting_pro"),
            "mode": extract(html, "net_setting_cs"),
            "port": extract(html, "net_setting_port"),
            "ip": extract(html, "net_setting_ip"),
            "timeout": extract(html, "net_setting_to"),
        }
        if any(v is None for v in cfg.values()):
            cfg = None
        return {"available": True, "status": status, "config": cfg, "detail": "OK"}, user, password
    except Exception as err:
        return {"available": False, "config": None, "detail": str(err)}, user, password


def snapshot(rep, title, host, user, password):
    rep.log("")
    rep.log("=" * 64)
    rep.log(title)
    rep.log("=" * 64)
    state = {
        "http80": tcp_open(host, 80),
        "p8899": tcp_open(host, PORT_ORIGINAL),
        "p8898": tcp_open(host, PORT_TEST),
    }
    rep.log(f"HTTP 80          : {'OPEN' if state['http80'] else 'CLOSED'}")
    rep.log(f"TCP 8899         : {'OPEN' if state['p8899'] else 'CLOSED'}")
    rep.log(f"TCP 8898         : {'OPEN' if state['p8898'] else 'CLOSED'}")
    hide, user, password = read_hide(host, user, password)
    state["hide"] = hide
    rep.log(f"hide_set_edit.html: {'AVAILABLE' if hide['available'] else 'UNAVAILABLE'}")
    if hide["available"] and hide["config"]:
        cfg = hide["config"]
        rep.log(f"Stored protocol  : {cfg['protocol']}")
        rep.log(f"Stored mode      : {cfg['mode']}")
        rep.log(f"Stored port      : {cfg['port']}")
        rep.log(f"Stored IP field  : {cfg['ip']}")
        rep.log(f"Stored timeout   : {cfg['timeout']}")
    elif not hide["available"]:
        rep.log(f"Hidden page detail: {hide['detail']}")
    return state, user, password


def base_config(state):
    cfg = state.get("hide", {}).get("config")
    if cfg:
        return {
            "protocol": cfg["protocol"],
            "mode": cfg["mode"],
            "ip": cfg["ip"],
            "timeout": cfg["timeout"],
        }
    return {"protocol": "TCP", "mode": "SERVER", "ip": "0.0.0.0", "timeout": "300"}


def set_port(host, port, cfg, user, password):
    selector = "TCPSERVER" if cfg["protocol"] == "TCP" and cfg["mode"] == "SERVER" else "TCPCLIENT"
    payload = urllib.parse.urlencode({
        "net_setting_pro": cfg["protocol"],
        "net_setting_cs": cfg["mode"],
        "net_setting_pro_sel": selector,
        "net_setting_port": str(port),
        "net_setting_ip": cfg["ip"],
        "net_setting_to": cfg["timeout"],
    }).encode()
    return request(
        f"http://{host}{COMMAND_PAGE}",
        method="POST",
        data=payload,
        user=user,
        password=password,
        referer=f"http://{host}{SETTING_PAGE}",
    )


def restart(host, user, password):
    payload = urllib.parse.urlencode({"HF_PROCESS_CMD": "RESTART"}).encode()
    return request(
        f"http://{host}{RESTART_PAGE}",
        method="POST",
        data=payload,
        user=user,
        password=password,
        referer=f"http://{host}{COMMAND_PAGE}",
    )


def ping(host):
    system = platform.system().lower()
    try:
        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", "1000", host]
        elif system == "darwin":
            cmd = ["ping", "-c", "1", "-W", "1000", host]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", host]
        return subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
        ).returncode == 0
    except Exception:
        return False


def wait_restart(rep, host, timeout=120):
    rep.log("Automatically monitoring restart...")
    deadline = time.time() + timeout
    saw_down = False
    while time.time() < deadline:
        if not ping(host) and not tcp_open(host, 80, 1):
            saw_down = True
            rep.log("Logger went offline.")
            break
        time.sleep(1)
    rep.log("Waiting for ping...")
    while time.time() < deadline:
        if ping(host):
            rep.log("Ping reply received.")
            break
        time.sleep(1)
    else:
        return saw_down, False
    rep.log("Waiting for HTTP port 80...")
    while time.time() < deadline:
        if tcp_open(host, 80, 1):
            rep.log("HTTP port 80 is back.")
            time.sleep(3)
            return saw_down, True
        time.sleep(1)
    return saw_down, False


def do_restart(rep, host, user, password):
    try:
        status, _, user, password = restart(host, user, password)
        rep.log(f"Restart request: HTTP {status}")
    except Exception as err:
        rep.log(f"Restart response not confirmed ({err}); monitoring continues.")
    _, back = wait_restart(rep, host)
    return back, user, password


def cfg_port(state):
    cfg = state.get("hide", {}).get("config")
    if not cfg:
        return None
    try:
        return int(cfg["port"])
    except Exception:
        return None


def finish(rep, code=0):
    path = rep.save()
    print(f"\nReport saved to: {path}")
    print("Please attach this .txt report to GitHub issue #128.")
    raise SystemExit(code)


def restore_8899(rep, host, state, user, password):
    rep.log("\nResume mode: 8898 is already stored or active.")
    if not confirm("Restore TCP port 8899 directly?"):
        finish(rep)
    cfg = base_config(state)
    try:
        status, _, user, password = set_port(host, 8899, cfg, user, password)
        rep.log(f"Store 8899: HTTP {status}")
    except Exception as err:
        rep.log(f"Restore failed: {err}")
        finish(rep, 10)
    current, user, password = snapshot(rep, "8899 STORED - BEFORE RESTART", host, user, password)
    if current["p8899"] and not current["p8898"]:
        if confirm("8899 is already active. Restart anyway to verify persistence?"):
            back, user, password = do_restart(rep, host, user, password)
            if not back:
                finish(rep, 11)
        else:
            finish(rep)
    else:
        if not confirm("Restart now to activate TCP port 8899?"):
            finish(rep)
        back, user, password = do_restart(rep, host, user, password)
        if not back:
            finish(rep, 12)
    final, user, password = snapshot(rep, "FINAL STATE AFTER RESTORING 8899", host, user, password)
    finish(rep, 0 if final["p8899"] else 13)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("host", nargs="?", default=DEFAULT_HOST)
    args = parser.parse_args()
    host = args.host
    user = password = None
    rep = Reporter()

    rep.log("TSUN Local - GEN4/1097 TCP port test")
    rep.log(f"Target logger: {host}")
    rep.log("No factory reset is performed.")
    rep.log("Port writes/restarts require confirmation; restart waiting is automatic.")

    if not confirm("Step 1: Check the current logger state?"):
        finish(rep)

    initial, user, password = snapshot(rep, "INITIAL STATE", host, user, password)

    if cfg_port(initial) == PORT_TEST or (initial["p8898"] and not initial["p8899"]):
        restore_8899(rep, host, initial, user, password)

    cfg = base_config(initial)

    if not confirm("Step 2: Store TCP port 8898?"):
        finish(rep)

    try:
        status, _, user, password = set_port(host, 8898, cfg, user, password)
        rep.log(f"Store 8898: HTTP {status}")
    except Exception as err:
        rep.log(f"Port write failed: {err}")
        finish(rep, 2)

    snapshot(rep, "8898 STORED - BEFORE RESTART", host, user, password)

    if not confirm("Step 3: Restart the logger to activate TCP port 8898?"):
        finish(rep)

    back, user, password = do_restart(rep, host, user, password)
    if not back:
        finish(rep, 3)

    active, user, password = snapshot(rep, "AFTER RESTART - 8898 SHOULD BE ACTIVE", host, user, password)

    if not confirm("Step 4: Restore TCP port 8899?"):
        finish(rep)

    try:
        status, _, user, password = set_port(host, 8899, cfg, user, password)
        rep.log(f"Store 8899: HTTP {status}")
    except Exception as err:
        rep.log(f"Restore failed: {err}")
        finish(rep, 4)

    snapshot(rep, "8899 STORED - BEFORE RESTART", host, user, password)

    if not confirm("Step 5: Restart the logger to activate TCP port 8899?"):
        finish(rep)

    back, user, password = do_restart(rep, host, user, password)
    if not back:
        finish(rep, 5)

    final, user, password = snapshot(rep, "FINAL STATE", host, user, password)

    rep.log("\nSummary:")
    rep.log(f"After 8898 restart: 8899={'OPEN' if active['p8899'] else 'CLOSED'}, 8898={'OPEN' if active['p8898'] else 'CLOSED'}")
    rep.log(f"Final state:        8899={'OPEN' if final['p8899'] else 'CLOSED'}, 8898={'OPEN' if final['p8898'] else 'CLOSED'}")
    finish(rep)


if __name__ == "__main__":
    main()

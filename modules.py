#!/data/data/com.termux/files/usr/bin/env python3
"""
Core modules for scans. Each module should be small and safe.
This file implements wrappers around system tools commonly available in Termux,
and some pure-python enrichments. Each module MUST validate input and limit
resource use. Add API-key-based enrichments (Shodan, Hunter, etc.) into a secure
secrets store before using.

Available modules (examples):
- whois
- dns: dig/resolve using dnspython
- nmap: runs nmap (basic scan)
- ping: ping host
"""

import shlex
import subprocess
import shutil
import socket
import time
import re
from typing import List
import whois
import dns.resolver

# whitelist allowed modules
AVAILABLE_MODULES = ["whois", "dns", "nmap", "ping"]

# Simple input validation: accept IPs, domains (letters, digits, - .)
_re_target = re.compile(r"^[A-Za-z0-9\.\-:]+$")

def _validate_target(t: str):
    if not t or not _re_target.match(t):
        raise ValueError("Invalid target")
    if len(t) > 253:
        raise ValueError("Target too long")

def run_module_safe(module: str, target: str) -> str:
    _validate_target(target)
    if module == "whois":
        return _mod_whois(target)
    if module == "dns":
        return _mod_dns(target)
    if module == "nmap":
        return _mod_nmap(target)
    if module == "ping":
        return _mod_ping(target)
    raise ValueError("Unknown module")

def _mod_whois(target: str) -> str:
    try:
        w = whois.whois(target)
        out = []
        for k, v in w.items():
            out.append(f"{k}: {v}")
        return "\n".join(out)
    except Exception as e:
        return f"whois error: {e}"

def _mod_dns(target: str) -> str:
    resolver = dns.resolver.Resolver()
    output = []
    try:
        for rtype in ("A","AAAA","MX","NS","TXT","SOA"):
            try:
                answers = resolver.resolve(target, rtype, lifetime=5)
                output.append(f"== {rtype} records ==")
                for a in answers:
                    output.append(str(a))
            except Exception:
                continue
        return "\n".join(output) if output else "No DNS records found or resolution failed."
    except Exception as e:
        return f"dns error: {e}"

def _mod_nmap(target: str) -> str:
    if not shutil.which("nmap"):
        return "nmap not installed (pkg install nmap)"
    # Basic TCP SYN scan limited to common ports; DO NOT do full aggressive scans without permission
    ports = "1-1024"
    cmd = ["nmap", "-sS", "-Pn", "-T4", "-p", ports, target]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return proc.stdout + ("\n\nSTDERR:\n" + proc.stderr if proc.stderr else "")

def _mod_ping(target: str) -> str:
    if ":" in target:
        # IPv6 ping not implemented here; fallback to socket check
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect((target, 80))
            sock.close()
            return "TCP/80 reachable (IPv6)"
        except Exception as e:
            return f"Unreachable: {e}"
    else:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect((target, 80))
            sock.close()
            return "TCP/80 reachable"
        except Exception as e:
            return f"Unreachable: {e}"
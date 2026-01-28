#!/data/data/com.termux/files/usr/bin/env python3
"""
Original core investigative modules implemented in pure Python.
- tcp_port_scan: concurrent TCP connect scanner (safe defaults)
- whois_query: minimal RFC-3912 WHOIS client (tries a few servers)
- http_enumeration: basic HTTP fetcher (headers, title, robots, sitemap)
- subdomain_bruteforce: wordlist-based resolver
"""
import socket
import concurrent.futures
import re
import httpx
from html import unescape
from typing import List

_re_target = re.compile(r"^[A-Za-z0-9\.\-:]+$")

def _validate_target(t: str):
    if not t or not _re_target.match(t) or len(t) > 253:
        raise ValueError("Invalid target")

def tcp_port_scan(target: str, ports: List[int], timeout: float = 1.0, max_workers: int = 50) -> str:
    _validate_target(target)
    results = []
    def check(p):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((target, p))
            s.close()
            return (p, True)
        except Exception:
            return (p, False)
    max_workers = max(1, min(max_workers, 200))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(check, p) for p in ports]
        for f in concurrent.futures.as_completed(futs):
            p, open_ = f.result()
            results.append(f"{p}: {'open' if open_ else 'closed'}")
    return "\n".join(sorted(results, key=lambda s: int(s.split(':')[0])))

def whois_query(domain: str, timeout: float = 5.0) -> str:
    _validate_target(domain)
    servers = ["whois.iana.org", "whois.verisign-grs.com", "whois.crsnic.net", "whois.arin.net"]
    q = domain + "\r\n"
    def query(server):
        try:
            s = socket.create_connection((server, 43), timeout=timeout)
            s.sendall(q.encode('utf-8'))
            out = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                out += chunk
            s.close()
            return out.decode('utf-8', errors='replace')
        except Exception:
            return None
    for s in servers:
        res = query(s)
        if res and len(res) > 0:
            return f"WHOIS from {s}:\n\n" + res
    raise RuntimeError("WHOIS failed (no server answered)")

def http_enumeration(target: str, timeout: float = 6.0) -> str:
    _validate_target(target)
    if not target.startswith("http"):
        url = "http://" + target
    else:
        url = target
    out = []
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(url)
            out.append(f"URL: {r.url}")
            out.append(f"Status: {r.status_code}")
            out.append("---- HEADERS ----")
            for k, v in r.headers.items():
                out.append(f"{k}: {v}")
            content = r.text[:200000]
            title = re.search(r'<title[^>]*>(.*?)</title>', content, re.I|re.S)
            if title:
                out.append("Title: " + unescape(title.group(1)).strip())
            # robots
            try:
                r2 = client.get(f"{r.url.scheme}://{r.url.host}/robots.txt")
                if r2.status_code == 200:
                    out.append("robots.txt:")
                    out.append(r2.text[:4000])
            except Exception:
                pass
            # sitemap suggestion
            sm = re.search(r'<loc>(https?://[^<]+)</loc>', content)
            if sm:
                out.append("Sitemap suggestion: " + sm.group(1))
            links = re.findall(r'href=["\'](.*?)["\']', content, re.I)
            out.append(f"Links found (sample up to 50): {len(links)}")
            out.append(", ".join(list(dict.fromkeys(links))[:50]))
    except Exception as e:
        out.append(f"HTTP error: {e}")
    return "\n".join(out)

def subdomain_bruteforce(domain: str, wordlist: List[str], timeout: float = 2.0, max_workers: int = 30) -> str:
    _validate_target(domain)
    results = []
    def try_sub(w):
        host = f"{w}.{domain}"
        try:
            addr = socket.gethostbyname(host)
            return f"{host} -> {addr}"
        except Exception:
            return None
    max_workers = max(1, min(max_workers, 200))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(try_sub, w.strip()) for w in wordlist if w.strip()]
        for f in concurrent.futures.as_completed(futs):
            r = f.result()
            if r:
                results.append(r)
    if not results:
        return "No subdomains found (or DNS blocked)"
    return "\n".join(sorted(results))
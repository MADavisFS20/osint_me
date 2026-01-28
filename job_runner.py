#!/data/data/com.termux/files/usr/bin/env python3
"""
Background job runner which executes a job and stores a Result row.
Design: run_job(engine, job_id)
"""
import time
from sqlmodel import Session
from models import Job, Result
from modules_core import tcp_port_scan, whois_query, http_enumeration, subdomain_bruteforce
import os

def run_job(engine, job_id: int):
    with Session(engine) as s:
        job = s.get(Job, job_id)
        if not job:
            return
        # mark running
        job.status = "running"
        job.started_at = time.time()
        s.add(job); s.commit()

    out = ""
    meta = {}
    try:
        if job.job_type == "tcp_scan":
            ports = list(range(1, 512))
            out = tcp_port_scan(job.target, ports, timeout=0.8, max_workers=80)
            meta["ports_scanned"] = len(ports)
        elif job.job_type == "whois":
            out = whois_query(job.target)
        elif job.job_type == "http_enum":
            out = http_enumeration(job.target)
        elif job.job_type == "sub_bruteforce":
            wl = []
            # load builtin wordlist
            wl_path = os.path.join(os.path.dirname(__file__), "..", "data", "subs.txt")
            try:
                with open(wl_path, "r") as f:
                    wl = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            except Exception:
                wl = ["www","api","mail","dev","test"]
            out = subdomain_bruteforce(job.target, wl, timeout=2.0, max_workers=40)
            meta["wordlist_count"] = len(wl)
        else:
            out = "Unknown job type"
            with Session(engine) as s:
                j = s.get(Job, job_id)
                j.status = "error"
                s.add(j); s.commit()
    except Exception as e:
        out = f"Error during job: {e}"
        with Session(engine) as s:
            j = s.get(Job, job_id)
            j.status = "error"
            s.add(j); s.commit()

    # store result
    with Session(engine) as s:
        j = s.get(Job, job_id)
        j.finished_at = time.time()
        if j.status != "error":
            j.status = "done"
        s.add(j); s.commit()
        res = Result(job_id=job_id, output=out, meta=meta)
        s.add(res); s.commit()
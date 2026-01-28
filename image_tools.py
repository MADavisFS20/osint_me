#!/data/data/com.termux/files/usr/bin/env python3
"""
Image utilities: download and compute perceptual hashes (pHash) to detect duplicates.
"""
import os
import httpx
from PIL import Image
import imagehash
from pathlib import Path
from typing import Optional

def download_image(url: str, dest_dir: str, timeout: float = 10.0) -> Optional[str]:
    os.makedirs(dest_dir, exist_ok=True)
    fname = os.path.basename(url.split("?")[0]) or f"image_{int(time.time())}"
    safe_name = fname.replace("/", "_")
    path = Path(dest_dir) / (safe_name)
    try:
        r = httpx.get(url, timeout=timeout)
        ctype = r.headers.get("content-type","")
        if r.status_code == 200 and ctype.startswith("image"):
            with open(path, "wb") as f:
                f.write(r.content)
            return str(path)
    except Exception:
        return None
    return None

def compute_phash(image_path: str) -> Optional[str]:
    try:
        img = Image.open(image_path)
        ph = imagehash.phash(img)
        return str(ph)
    except Exception:
        return None

def find_duplicates_in_dir(directory: str, hashfunc=compute_phash):
    files = []
    for root, _, filenames in os.walk(directory):
        for fn in filenames:
            fp = os.path.join(root, fn)
            if fn.lower().endswith((".png",".jpg",".jpeg",".gif",".webp")):
                ph = hashfunc(fp)
                if ph:
                    files.append((fp, ph))
    groups = {}
    for fp, ph in files:
        groups.setdefault(ph, []).append(fp)
    return {k: v for k, v in groups.items() if len(v) > 1}
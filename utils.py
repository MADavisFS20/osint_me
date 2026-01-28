#!/data/data/com.termux/files/usr/bin/env python3
"""
Utility helpers: safe filenames, path helpers, secret generation.
"""
import os
import re
import secrets
import string

def safe_filename(name: str) -> str:
    """
    Sanitize a filename by removing dangerous characters.
    """
    name = os.path.basename(name)
    # replace spaces and control chars
    name = re.sub(r'[^A-Za-z0-9._\-]', '_', name)
    return name[:255]

def ensure_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def generate_secret(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
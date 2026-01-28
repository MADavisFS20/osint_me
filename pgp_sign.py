#!/data/data/com.termux/files/usr/bin/env python3
"""
PGP signing helper that wraps GPG (if available).
- sign_file(file_path, key_id=None) -> returns signature path or None
Note: This helper calls the system gpg binary. Ensure gnupg is installed and a key is available.
"""
import shutil
import subprocess
import os
from typing import Optional

def is_gpg_available() -> bool:
    return shutil.which("gpg") is not None

def sign_file(file_path: str, key_id: Optional[str] = None) -> Optional[str]:
    """
    Create a detached signature (binary) and return its path.
    If --armor is desired, change args accordingly.
    """
    if not is_gpg_available():
        return None
    sig_path = file_path + ".sig"
    cmd = ["gpg", "--batch", "--yes", "--output", sig_path, "--detach-sign"]
    if key_id:
        cmd.extend(["--local-user", key_id])
    cmd.append(file_path)
    # This will prompt for passphrase if key requires it - recommend using an agent or unlocked key
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # failed to sign
        return None
    return sig_path
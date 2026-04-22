#!/usr/bin/env python3
"""Shared SSH config + connection helpers for VPS scripts."""

from __future__ import annotations

import os
from pathlib import Path

import paramiko


def load_vps_config() -> tuple[str, str, int]:
    host = os.getenv("VPS_HOST", "147.93.156.165").strip()
    user = os.getenv("VPS_USER", "root").strip()
    try:
        port = int(os.getenv("VPS_PORT", "22").strip() or "22")
    except Exception:
        port = 22
    return host, user, port


def connect_ssh(*, host: str | None = None, user: str | None = None, port: int | None = None, timeout: int = 10) -> paramiko.SSHClient:
    resolved_host, resolved_user, resolved_port = load_vps_config()
    host = (host or resolved_host).strip()
    user = (user or resolved_user).strip()
    port = int(port or resolved_port)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key_path = (os.getenv("VPS_SSH_KEY") or "").strip()
    password = <REDACTED_PASSWORD>"VPS_PASSWORD") or "").strip()

    if key_path:
        key_file = Path(key_path).expanduser()
        if not key_file.exists():
            raise RuntimeError(f"VPS_SSH_KEY path does not exist: {key_file}")
        ssh.connect(host, port=port, username=user, key_filename=str(key_file), timeout=timeout)
        return ssh

    if password:
        ssh.connect(host, port=port, username=user, password=<REDACTED_PASSWORD> timeout=timeout)
        return ssh

    raise RuntimeError(
        "Missing VPS credentials. Set VPS_PASSWORD or VPS_SSH_KEY (recommended) with VPS_HOST/VPS_USER/VPS_PORT as needed."
    )


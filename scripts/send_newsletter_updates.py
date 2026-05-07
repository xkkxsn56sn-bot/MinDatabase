#!/usr/bin/env python3
"""Send newsletter update notifications for new/modified content entries.

This script reads:
- assets/data/push_notices.json (latest content updates)
- newsletter_subscribers.csv (recipient list)

It sends an email to all subscribers when a new update signature appears,
and stores the last-sent signature in assets/data/newsletter_last_notified.json.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTICES_PATH = REPO_ROOT / "assets" / "data" / "push_notices.json"
SUBSCRIBERS_PATH = REPO_ROOT / "newsletter_subscribers.csv"
STATE_PATH = REPO_ROOT / "assets" / "data" / "newsletter_last_notified.json"


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_port(value: str | None, fallback: int) -> int:
    if not value or not value.strip():
        return fallback
    try:
        return int(value.strip())
    except ValueError:
        return fallback


def _derive_smtp_host_from_imap(imap_host: str | None) -> str:
    host = (imap_host or "").strip()
    if not host:
        return ""
    if host.startswith("imap."):
        return "smtp." + host[len("imap."):]
    return host


def _load_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _load_recipients(path: Path) -> list[str]:
    if not path.exists():
        return []

    seen: set[str] = set()
    recipients: list[str] = []

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            email_value = (row.get("email") or "").strip().lower()
            if not email_value or "@" not in email_value:
                continue
            if email_value in seen:
                continue
            seen.add(email_value)
            recipients.append(email_value)

    return recipients


def _signature_for_notices(notices: Iterable[dict]) -> str:
    parts: list[str] = []
    for notice in notices:
        parts.append(
            "|".join(
                [
                    str(notice.get("path") or ""),
                    str(notice.get("pushed_at") or ""),
                    str(notice.get("change_type") or ""),
                ]
            )
        )
    return "\n".join(parts)


def _change_label(change_type: str) -> str:
    return "New" if str(change_type).strip().lower() == "created" else "Updated"


def _build_message(subject: str, sender: str, recipient: str, notices: list[dict], site_base_url: str) -> EmailMessage:
    lines_text: list[str] = [
        "Medieval Visions content update",
        "",
        "The following entries were recently added or modified:",
        "",
    ]
    lines_html: list[str] = [
        "<p><strong>Medieval Visions content update</strong></p>",
        "<p>The following entries were recently added or modified:</p>",
        "<ul>",
    ]

    for notice in notices:
        title = str(notice.get("title") or "Untitled")
        section = str(notice.get("section") or "Other")
        change_type = _change_label(str(notice.get("change_type") or "modified"))
        page_url = str(notice.get("page_url") or "/")
        if page_url.startswith("http://") or page_url.startswith("https://"):
            href = page_url
        else:
            href = f"{site_base_url.rstrip('/')}/{page_url.lstrip('/')}"

        lines_text.append(f"- [{change_type}] {title} ({section}) -> {href}")
        lines_html.append(f"<li><strong>{change_type}</strong> {title} ({section}) - <a href=\"{href}\">Open entry</a></li>")

    lines_text.extend(
        [
            "",
            "You are receiving this because you subscribed on medievalvisions.com.",
            "For support, contact: contact@medievalvisions.com",
        ]
    )
    lines_html.extend(
        [
            "</ul>",
            "<p>You are receiving this because you subscribed on medievalvisions.com.</p>",
            "<p>For support, contact: <a href=\"mailto:contact@medievalvisions.com\">contact@medievalvisions.com</a></p>",
        ]
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content("\n".join(lines_text))
    msg.add_alternative("\n".join(lines_html), subtype="html")
    return msg


def _send_messages(
    host: str,
    port: int,
    username: str | None,
    password: str | None,
    sender: str,
    notices: list[dict],
    recipients: list[str],
    subject: str,
    site_base_url: str,
    use_ssl: bool,
    use_starttls: bool,
) -> int:
    if use_ssl:
        server: smtplib.SMTP | smtplib.SMTP_SSL
        server = smtplib.SMTP_SSL(host, port, timeout=30, context=ssl.create_default_context())
    else:
        server = smtplib.SMTP(host, port, timeout=30)

    sent = 0
    try:
        server.ehlo()
        if use_starttls and not use_ssl:
            server.starttls(context=ssl.create_default_context())
            server.ehlo()

        if username and password:
            server.login(username, password)

        for recipient in recipients:
            msg = _build_message(subject, sender, recipient, notices, site_base_url)
            server.send_message(msg)
            sent += 1
    finally:
        server.quit()

    return sent


def main() -> int:
    notices_json = _load_json(NOTICES_PATH, {"notices": []})
    notices = notices_json.get("notices") or []
    if not notices:
        print("No notices found. Skipping newsletter notification.")
        return 0

    state = _load_json(STATE_PATH, {})
    current_signature = _signature_for_notices(notices)
    force_notify = _parse_bool(os.getenv("FORCE_NOTIFY"), default=False)

    if not force_notify and state.get("last_signature") == current_signature:
        print("Latest notices were already notified. Skipping.")
        return 0

    recipients = _load_recipients(SUBSCRIBERS_PATH)
    recipient_override = (os.getenv("NEWSLETTER_RECIPIENT_OVERRIDE") or "").strip()
    if recipient_override:
        print("NEWSLETTER_RECIPIENT_OVERRIDE is set; using override recipients only.")
        recipients = [item.strip().lower() for item in recipient_override.split(",") if item.strip()]

    if not recipients:
        print("No recipients found in newsletter_subscribers.csv. Skipping.")
        return 0

    print(f"Resolved {len(recipients)} newsletter recipient(s).")

    imap_host = (os.getenv("IMAP_HOST") or "").strip()
    imap_username = (os.getenv("IMAP_USERNAME") or "").strip() or None
    imap_password = (os.getenv("IMAP_PASSWORD") or "").strip() or None

    host = (os.getenv("SMTP_HOST") or "").strip() or _derive_smtp_host_from_imap(imap_host)
    username = (os.getenv("SMTP_USERNAME") or "").strip() or imap_username
    password = (os.getenv("SMTP_PASSWORD") or "").strip() or imap_password
    sender = (os.getenv("SMTP_FROM") or username or "contact@medievalvisions.com").strip()
    subject = (os.getenv("NEWSLETTER_SUBJECT") or "Medieval Visions update").strip()
    site_base_url = (os.getenv("SITE_BASE_URL") or "https://medievalvisions.com").strip()
    secure_mode = (os.getenv("SMTP_SECURE") or "starttls").strip().lower()

    if not host:
        print("SMTP_HOST not configured. Skipping newsletter notification.")
        return 0

    use_ssl = secure_mode == "ssl"
    use_starttls = secure_mode != "ssl"
    default_port = 465 if use_ssl else 587
    port = _parse_port(os.getenv("SMTP_PORT"), default_port)

    try:
        sent_count = _send_messages(
            host=host,
            port=port,
            username=username,
            password=password,
            sender=sender,
            notices=notices,
            recipients=recipients,
            subject=subject,
            site_base_url=site_base_url,
            use_ssl=use_ssl,
            use_starttls=use_starttls,
        )
    except Exception as exc:
        print(f"Failed to send newsletter notifications: {exc}")
        return 1

    now_iso = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    state_payload = {
        "last_sent_at": now_iso,
        "last_signature": current_signature,
        "last_notice_count": len(notices),
        "last_recipient_count": len(recipients),
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(f"Sent newsletter update to {sent_count} recipient(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

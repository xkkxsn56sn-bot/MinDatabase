#!/usr/bin/env python3
"""Sync newsletter subscribers from inbox emails into CSV.

This script is designed for CI automation (GitHub Actions):
- Connect to an IMAP inbox
- Read unseen messages matching a subject filter
- Extract e-mail addresses from the message body
- Append unique addresses to newsletter_subscribers.csv
"""

from __future__ import annotations

import csv
import datetime as dt
import email
import imaplib
import os
import re
import sys
from email.header import decode_header
from email.message import Message
from pathlib import Path
from typing import Iterable

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
DEFAULT_EXCLUDES = {
    "contact@medievalvisions.com",
    "noreply@formsubmit.co",
    "no-reply@formsubmit.co",
}


def _parse_imap_port(raw: str | None) -> int:
    if not raw or not raw.strip():
        return 993
    try:
        return int(raw.strip())
    except ValueError:
        print("Invalid IMAP_PORT value. Falling back to 993.", file=sys.stderr)
        return 993


def _decode_header_value(raw: str | None) -> str:
    if not raw:
        return ""
    parts = decode_header(raw)
    decoded: list[str] = []
    for value, charset in parts:
        if isinstance(value, bytes):
            decoded.append(value.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(value)
    return "".join(decoded)


def _extract_text_parts(message: Message) -> list[str]:
    text_parts: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = (part.get("Content-Disposition") or "").lower()
            if "attachment" in content_disposition:
                continue
            if content_type in {"text/plain", "text/html"}:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text_parts.append(payload.decode(charset, errors="replace"))
    else:
        payload = message.get_payload(decode=True)
        if payload:
            charset = message.get_content_charset() or "utf-8"
            text_parts.append(payload.decode(charset, errors="replace"))
    return text_parts


def _extract_candidate_emails(text_chunks: Iterable[str]) -> set[str]:
    candidates: set[str] = set()
    for chunk in text_chunks:
        lowered = chunk.lower()

        # Prefer values explicitly associated with an email field if present.
        contextual_matches = re.findall(
            r"(?:^|\n|\r)\s*email\s*[:|\-]?\s*([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
            lowered,
            flags=re.IGNORECASE,
        )
        candidates.update(contextual_matches)

        generic_matches = EMAIL_PATTERN.findall(lowered)
        candidates.update(generic_matches)

    return {item.strip().lower() for item in candidates if item.strip()}


def _load_existing_emails(csv_path: Path) -> set[str]:
    if not csv_path.exists():
        return set()

    known: set[str] = set()
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            value = (row.get("email") or "").strip().lower()
            if value:
                known.add(value)
    return known


def _append_rows(csv_path: Path, rows: list[list[str]]) -> None:
    csv_exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if not csv_exists:
            writer.writerow(["email", "consent", "source", "created_at", "notes"])
        writer.writerows(rows)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "newsletter_subscribers.csv"

    imap_host = os.getenv("IMAP_HOST")
    imap_port = _parse_imap_port(os.getenv("IMAP_PORT"))
    imap_username = os.getenv("IMAP_USERNAME")
    imap_password = os.getenv("IMAP_PASSWORD")
    subject_filter = os.getenv("SUBSCRIBER_MAIL_SUBJECT", "Medieval Visions newsletter registration")

    if not all([imap_host, imap_username, imap_password]):
        print("Skipping sync: IMAP_HOST, IMAP_USERNAME, or IMAP_PASSWORD is not configured.")
        return 0

    excludes = set(DEFAULT_EXCLUDES)
    extra_excludes_raw = os.getenv("EXCLUDE_EMAILS", "")
    if extra_excludes_raw.strip():
        excludes.update({item.strip().lower() for item in extra_excludes_raw.split(",") if item.strip()})

    known_emails = _load_existing_emails(csv_path)
    rows_to_append: list[list[str]] = []

    try:
        mailbox = imaplib.IMAP4_SSL(imap_host, imap_port)
    except Exception as exc:
        print(f"Could not connect to IMAP server {imap_host}:{imap_port}: {exc}", file=sys.stderr)
        return 1

    try:
        try:
            mailbox.login(imap_username, imap_password)
        except Exception as exc:
            print(f"IMAP login failed: {exc}", file=sys.stderr)
            return 1

        select_status, _ = mailbox.select("INBOX")
        if select_status != "OK":
            print("Could not select INBOX.", file=sys.stderr)
            return 1

        # Search unseen messages first, then filter by decoded subject in Python.
        # This is more resilient to IMAP server search quirks/encodings.
        status, ids = mailbox.search(None, "UNSEEN")
        if status != "OK":
            print("Could not search mailbox.", file=sys.stderr)
            return 1

        message_ids = ids[0].split()
        if not message_ids:
            print("No new subscriber emails found.")
            return 0

        now_iso = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

        for message_id in message_ids:
            try:
                fetch_status, payload = mailbox.fetch(message_id, "(BODY.PEEK[])")
            except Exception as exc:
                print(f"Failed to fetch message {message_id!r}: {exc}", file=sys.stderr)
                continue

            if fetch_status != "OK" or not payload or payload[0] is None:
                continue

            raw_bytes = payload[0][1]
            if not isinstance(raw_bytes, (bytes, bytearray)):
                continue

            message = email.message_from_bytes(raw_bytes)
            message_subject = _decode_header_value(message.get("Subject"))
            if subject_filter.lower() not in message_subject.lower():
                continue

            text_chunks = _extract_text_parts(message)
            found = _extract_candidate_emails(text_chunks)

            new_count = 0
            for email_value in sorted(found):
                if email_value in excludes or email_value in known_emails:
                    continue
                known_emails.add(email_value)
                rows_to_append.append(
                    [
                        email_value,
                        "yes",
                        "formsubmit_email",
                        now_iso,
                        f"subject={message_subject}",
                    ]
                )
                new_count += 1

            # Mark targeted messages as seen once successfully processed.
            mailbox.store(message_id, "+FLAGS", "\\Seen")

        if not rows_to_append:
            print("No new unique subscribers to append.")
            return 0

        _append_rows(csv_path, rows_to_append)
        print(f"Appended {len(rows_to_append)} new subscriber(s) to {csv_path.name}.")
        return 0
    finally:
        try:
            mailbox.close()
        except Exception:
            pass
        mailbox.logout()


if __name__ == "__main__":
    raise SystemExit(main())

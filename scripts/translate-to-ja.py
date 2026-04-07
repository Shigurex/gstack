#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import List, Tuple

try:
    from mtranslate import translate as mtranslate
except Exception as e:  # pragma: no cover
    print(f"Failed to import mtranslate: {e}", file=sys.stderr)
    sys.exit(1)

TOKEN_PREFIX = "⟪GS_TOK_"
TOKEN_SUFFIX = "⟫"

_ORIG_URLOPEN = urllib.request.urlopen


class TranslateTimeoutError(Exception):
    pass


def _timeout_handler(_signum, _frame):
    raise TranslateTimeoutError()


def translate_with_timeout(text: str, timeout_sec: int = 4) -> str:
    # SIGALRM is available on Unix-like systems (Codex desktop runs on macOS/Linux).
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout_sec)
    try:
        return mtranslate(text, "ja", "en")
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def urlopen_with_default_timeout(*args, **kwargs):
    kwargs.setdefault("timeout", 4)
    return _ORIG_URLOPEN(*args, **kwargs)

def run_rg_files(root: Path, patterns: List[str]) -> List[Path]:
    cmd = ["rg", "--files"]
    for p in patterns:
        cmd.extend(["-g", p])
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, check=True)
    files = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        path = root / line
        # Exclude vendored/generated binary-ish paths that should not be touched.
        if "design-html/vendor/" in line:
            continue
        files.append(path)
    files.sort(key=lambda p: p.stat().st_size if p.exists() else 0)
    return files


def protect_patterns(text: str) -> Tuple[str, List[str]]:
    tokens: List[str] = []

    def repl(match: re.Match[str]) -> str:
        idx = len(tokens)
        tokens.append(match.group(0))
        return f"{TOKEN_PREFIX}{idx}{TOKEN_SUFFIX}"

    # Fenced code blocks first (including language fences).
    text = re.sub(r"```[\s\S]*?```", repl, text)
    # Inline code.
    text = re.sub(r"`[^`\n]+`", repl, text)
    # Raw URLs.
    text = re.sub(r"https?://[^\s)]+", repl, text)
    # Markdown link/reference definitions urls: [id]: url "title"
    text = re.sub(r"^\s*\[[^\]]+\]:\s+\S+.*$", repl, text, flags=re.MULTILINE)
    return text, tokens


def restore_patterns(text: str, tokens: List[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        m = re.search(r"(\d+)", raw)
        if not m:
            return raw
        idx = int(m.group(1))
        if 0 <= idx < len(tokens):
            return tokens[idx]
        return raw

    pattern = re.compile(re.escape(TOKEN_PREFIX) + r"\s*(\d+)\s*" + re.escape(TOKEN_SUFFIX), flags=re.IGNORECASE)
    return pattern.sub(repl, text)


def should_translate(chunk: str) -> bool:
    # Skip chunks without latin letters.
    return bool(re.search(r"[A-Za-z]", chunk))


def split_large_chunk(chunk: str, max_len: int = 2000) -> List[str]:
    if len(chunk) <= max_len:
        return [chunk]
    # Keep paragraph boundaries where possible.
    parts: List[str] = []
    current = []
    current_len = 0
    for para in re.split(r"(\n\n+)", chunk):
        if current_len + len(para) > max_len and current:
            parts.append("".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)
    if current:
        parts.append("".join(current))
    # If still too big, split by lines to avoid breaking placeholder tokens.
    final: List[str] = []
    for p in parts:
        if len(p) <= max_len:
            final.append(p)
            continue

        line_buf: List[str] = []
        line_len = 0
        for line in re.split(r"(\n)", p):
            if line_len + len(line) > max_len and line_buf:
                final.append("".join(line_buf))
                line_buf = [line]
                line_len = len(line)
            else:
                line_buf.append(line)
                line_len += len(line)
        if line_buf:
            final.append("".join(line_buf))

    return final


def translate_text(
    text: str,
    sleep_sec: float,
    file_timeout_sec: int,
    request_timeout_sec: int,
    max_chunk_len: int,
    show_progress: bool,
) -> str:
    protected, tokens = protect_patterns(text)
    started_at = time.monotonic()

    chunks = re.split(r"(\n\n+)", protected)
    out: List[str] = []
    translatable_total = sum(
        1 for ch in chunks if ch and not ch.startswith("\n\n") and should_translate(ch)
    )
    translatable_done = 0

    for ch in chunks:
        if time.monotonic() - started_at > file_timeout_sec:
            raise TranslateTimeoutError(f"file translation timed out after {file_timeout_sec}s")

        if ch.startswith("\n\n") or ch == "":
            out.append(ch)
            continue

        if not should_translate(ch):
            out.append(ch)
            continue

        translated_parts: List[str] = []
        for piece in split_large_chunk(ch, max_len=max_chunk_len):
            if time.monotonic() - started_at > file_timeout_sec:
                raise TranslateTimeoutError(f"file translation timed out after {file_timeout_sec}s")

            if not should_translate(piece):
                translated_parts.append(piece)
                continue
            last_err = None
            for _ in range(1):
                try:
                    translated = translate_with_timeout(piece, timeout_sec=request_timeout_sec)
                    translated_parts.append(translated)
                    last_err = None
                    break
                except Exception as e:  # pragma: no cover
                    last_err = e
                    time.sleep(max(0.5, sleep_sec))
            if last_err is not None:
                translated_parts.append(piece)
        out.append("".join(translated_parts))
        translatable_done += 1
        if show_progress and (translatable_done % 20 == 0 or translatable_done == translatable_total):
            elapsed = int(time.monotonic() - started_at)
            print(
                f"  progress: {translatable_done}/{translatable_total} chunks ({elapsed}s)",
                flush=True,
            )
        if sleep_sec > 0:
            time.sleep(sleep_sec)

    translated_text = "".join(out)
    translated_text = restore_patterns(translated_text, tokens)
    return translated_text


def process_file(
    path: Path,
    sleep_sec: float,
    dry_run: bool,
    file_timeout_sec: int,
    request_timeout_sec: int,
    max_chunk_len: int,
    show_progress: bool,
) -> bool:
    original = path.read_text(encoding="utf-8")
    translated = translate_text(
        original,
        sleep_sec,
        file_timeout_sec,
        request_timeout_sec,
        max_chunk_len,
        show_progress,
    )
    if translated == original:
        return False
    if not dry_run:
        path.write_text(translated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Translate markdown/template files to Japanese.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--sleep", type=float, default=0.1, help="Sleep between requests")
    parser.add_argument("--file-timeout", type=int, default=240, help="Per-file timeout in seconds")
    parser.add_argument("--request-timeout", type=int, default=4, help="Per-request timeout in seconds")
    parser.add_argument("--max-chunk-len", type=int, default=2000, help="Chunk size before splitting")
    parser.add_argument("--show-progress", action="store_true", help="Print in-file progress")
    parser.add_argument("--dry-run", action="store_true", help="Show files that would change")
    parser.add_argument("--pattern", action="append", help="Glob patterns passed to rg --files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    urllib.request.urlopen = urlopen_with_default_timeout
    patterns = args.pattern if args.pattern else ["*.md", "*.md.tmpl"]
    files = run_rg_files(root, patterns)

    changed = 0
    for i, path in enumerate(files, start=1):
        try:
            print(f"[{i}/{len(files)}] processing: {path.relative_to(root)}", flush=True)
            did_change = process_file(
                path,
                args.sleep,
                args.dry_run,
                args.file_timeout,
                args.request_timeout,
                args.max_chunk_len,
                args.show_progress,
            )
            status = "changed" if did_change else "unchanged"
            if did_change:
                changed += 1
            print(f"[{i}/{len(files)}] {status}: {path.relative_to(root)}", flush=True)
        except Exception as e:
            print(f"[{i}/{len(files)}] error: {path.relative_to(root)} -> {e}", file=sys.stderr, flush=True)

    print(f"Done. changed={changed}, total={len(files)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

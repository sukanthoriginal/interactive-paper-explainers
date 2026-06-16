"""
Tiny single-file server for the Claude Feedback library.

Serves a directory of HTML artifacts AND accepts comment-batch submissions from
the in-page library. Submissions are appended to <artifact>/feedback/inbox.jsonl
where Claude (the agent) can pick them up, process them, and append to
<artifact>/feedback/history.json. The page polls history.json to detect new
changes and offer a walkthrough.

Usage:
    python lib/server.py <artifact_dir> [--port 5050]

There are NO dependencies beyond the Python standard library.
"""
import argparse
import http.server
import importlib.util
import json
import mimetypes
import os
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

# Project-root lib directory (where this file lives). The server serves
# /lib/<file> from here so artifacts can <script src="/lib/feedback.js">
# instead of inlining — library updates apply on a simple page refresh.
LIB_DIR = Path(__file__).resolve().parent
REPO_ROOT = LIB_DIR.parent
PUBLISH_SCRIPT = REPO_ROOT / "scripts" / "publish_pages.py"

# ---------- Auto-shutdown bookkeeping ----------
# Servers launched as Claude Code background tasks would otherwise outlive the
# session (orphaned to launchd/init) and accumulate. Two complementary checks:
#   1. parent-death — if our parent process exits, we get reparented to PID 1.
#      Skip this watchdog if we were already detached at startup (e.g. nohup).
#   2. idle timeout — the page polls every ~4s, so any live browser keeps us
#      alive. When no requests have arrived for IDLE_TIMEOUT_S, exit.
INITIAL_PPID = os.getppid()
_activity_lock = threading.Lock()
_last_activity = time.monotonic()
_codex_auto_config = {
    "enabled": False,
    "codex_bin": "codex",
    "artifact_dir": None,
}
_codex_auto_lock = threading.Lock()
_codex_auto_running = False
_codex_auto_run_again = False
_publish_lock = threading.Lock()
_publish_module = None


def _touch_activity():
    global _last_activity
    with _activity_lock:
        _last_activity = time.monotonic()


def _idle_seconds():
    with _activity_lock:
        return time.monotonic() - _last_activity


def _trigger_codex_auto_process():
    """Start one Codex feedback-processing run, coalescing bursts of submits."""
    global _codex_auto_running, _codex_auto_run_again
    if not _codex_auto_config["enabled"]:
        return
    with _codex_auto_lock:
        if _codex_auto_running:
            _codex_auto_run_again = True
            return
        _codex_auto_running = True
    threading.Thread(target=_codex_auto_process_loop, daemon=True).start()


def _codex_auto_process_loop():
    global _codex_auto_running, _codex_auto_run_again
    while True:
        _run_codex_auto_process_once()
        with _codex_auto_lock:
            if _codex_auto_run_again:
                _codex_auto_run_again = False
                continue
            _codex_auto_running = False
            return


def _run_codex_auto_process_once():
    artifact_dir = _codex_auto_config["artifact_dir"]
    if artifact_dir is None:
        return
    feedback_dir = artifact_dir / "feedback"
    log_path = feedback_dir / "codex-auto.log"
    prompt = f"""Process submitted feedback for this interactive paper explainer.

Paths:
- Explainer HTML: {artifact_dir / "index.html"}
- Feedback inbox: {feedback_dir / "inbox.jsonl"}
- Feedback history: {feedback_dir / "history.json"}

Treat a comment as already processed if any existing history[].changes[].in_response_to[] contains that comment id. For each unprocessed comment, inspect index.html, make the smallest helpful edit to answer or address the feedback, add a data-cf-change="ch-..." anchor to the changed element, and append a history batch entry to history.json.

Quality bar for explanation feedback:
- Take the user's wording literally. If they ask for a visual, illustration, diagram, exact example, first-principles explanation, or say they do not understand, make an actual structural visual/interactive HTML+CSS change rather than another paragraph or table.
- Prefer a paper-grounded teaching board: show the concrete object first, then map visible input -> hidden representation -> score/output. Use exact paper facts such as figure crops, table values, data shapes, channel names, sample rates, model names, and source constraints.
- Remove vague filler unless it is unpacked visually. Phrases like "pixels/features", "selected channels", "embedding", "score", or "samples" must be illustrated with a concrete mapping when the user asks about them.
- Preserve existing data-cf-change anchors that the browser/history already targets, and add a new anchor only for a major upgrade.

The history entry must include the original comments and changes entries containing id, title, anchor, and in_response_to. If an edit is made for a comment, that comment id must be recorded in history.json before finishing. If there are no unprocessed comments, do not edit files and do not append history. Keep the final response brief."""
    cmd = [
        _codex_auto_config["codex_bin"],
        "-c",
        'model_reasoning_effort="medium"',
        "-c",
        'model_reasoning_summary="none"',
        "--sandbox",
        "workspace-write",
        "--cd",
        str(artifact_dir),
        "exec",
        "--skip-git-repo-check",
        prompt,
    ]
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n[codex-auto] {time.strftime('%Y-%m-%dT%H:%M:%S')} starting\n")
        log.flush()
        try:
            result = subprocess.run(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=900,
                check=False,
            )
            log.write(f"[codex-auto] exit={result.returncode}\n")
        except Exception as exc:
            log.write(f"[codex-auto] failed: {exc}\n")
        log.flush()


def _has_unprocessed_feedback(feedback_dir: Path) -> bool:
    inbox = feedback_dir / "inbox.jsonl"
    history = feedback_dir / "history.json"
    if not inbox.exists():
        return False
    try:
        batches = [
            json.loads(line)
            for line in inbox.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        history_batches = json.loads(history.read_text(encoding="utf-8")) if history.exists() else []
    except Exception:
        return True

    handled = {
        comment_id
        for batch in history_batches
        for change in batch.get("changes", [])
        for comment_id in change.get("in_response_to", [])
    }
    for batch in batches:
        for comment in batch.get("comments", []):
            if comment.get("id") not in handled:
                return True
    return False


def _load_publish_module():
    global _publish_module
    if _publish_module is not None:
        return _publish_module
    if not PUBLISH_SCRIPT.exists():
        raise FileNotFoundError(f"publish helper not found: {PUBLISH_SCRIPT}")
    spec = importlib.util.spec_from_file_location("ipe_publish_pages", PUBLISH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load publish helper: {PUBLISH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _publish_module = module
    return module


def _paper_slug(artifact_dir: Path) -> str:
    module = _load_publish_module()
    return module.normalize_slug(artifact_dir.name)


def _iter_asset_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        p.relative_to(root)
        for p in root.rglob("*")
        if p.is_file() and p.name != ".DS_Store"
    )


def _assets_differ(source_assets: Path, target_assets: Path) -> bool:
    source_files = _iter_asset_files(source_assets)
    target_files = _iter_asset_files(target_assets)
    if source_files != target_files:
        return True
    for rel in source_files:
        if (source_assets / rel).read_bytes() != (target_assets / rel).read_bytes():
            return True
    return False


def _run_repo_cmd(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )


def _publish_scope(slug: str) -> list[str]:
    return [
        ".nojekyll",
        "index.html",
        f"papers/{slug}",
        "scripts/publish_pages.py",
    ]


def _git_branch() -> str:
    result = _run_repo_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else "main"


def _git_ahead_count() -> int:
    result = _run_repo_cmd(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if result.returncode != 0:
        return 0
    upstream = result.stdout.strip()
    if not upstream:
        return 0
    result = _run_repo_cmd(["git", "rev-list", "--count", f"{upstream}..HEAD"])
    if result.returncode != 0:
        return 0
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


def _git_dirty_lines(slug: str) -> list[str]:
    result = _run_repo_cmd(["git", "status", "--porcelain", "--", *_publish_scope(slug)])
    if result.returncode != 0:
        return [result.stdout.strip()]
    return [line for line in result.stdout.splitlines() if line.strip()]


def _publish_status_payload(artifact_dir: Path, publishing: bool | None = None) -> dict:
    module = _load_publish_module()
    slug = _paper_slug(artifact_dir)
    source_html = artifact_dir / "index.html"
    target_dir = REPO_ROOT / "papers" / slug
    target_html = target_dir / "index.html"

    html_stale = True
    if source_html.exists() and target_html.exists():
        expected = module.publicize_html(source_html.read_text(encoding="utf-8"))
        html_stale = target_html.read_text(encoding="utf-8", errors="replace") != expected

    assets_stale = _assets_differ(artifact_dir / "assets", target_dir / "assets")
    static_stale = html_stale or assets_stale or not target_html.exists()
    dirty_lines = _git_dirty_lines(slug)
    ahead_count = _git_ahead_count()
    is_publishing = _publish_lock.locked() if publishing is None else publishing
    can_publish = (static_stale or bool(dirty_lines) or ahead_count > 0) and not is_publishing

    if is_publishing:
        state = "publishing"
        message = "publishing this explainer..."
    elif static_stale:
        state = "ready"
        message = "this explainer has unpublished changes"
    elif dirty_lines:
        state = "ready"
        message = "this explainer is ready to commit"
    elif ahead_count > 0:
        state = "ready"
        message = "this explainer is ready to push"
    else:
        state = "up_to_date"
        message = "this explainer is already published"

    return {
        "ok": True,
        "slug": slug,
        "state": state,
        "message": message,
        "can_publish": can_publish,
        "static_stale": static_stale,
        "html_stale": html_stale,
        "assets_stale": assets_stale,
        "dirty": dirty_lines,
        "ahead_count": ahead_count,
        "branch": _git_branch(),
        "target_dir": str(target_dir),
    }


def _same_origin_or_no_origin(handler: http.server.BaseHTTPRequestHandler) -> bool:
    origin = handler.headers.get("Origin")
    if not origin:
        return True
    host = handler.headers.get("Host", "")
    parsed = urlparse(origin)
    return parsed.scheme in ("http", "https") and parsed.netloc == host


def _publish_now(artifact_dir: Path) -> dict:
    if not _publish_lock.acquire(blocking=False):
        return {"ok": False, "error": "publish already running"}
    try:
        before = _publish_status_payload(artifact_dir, publishing=False)
        slug = before["slug"]
        output: list[str] = []

        if before["static_stale"]:
            result = _run_repo_cmd([sys.executable, str(PUBLISH_SCRIPT), str(artifact_dir), "--slug", slug], timeout=120)
            output.append(result.stdout.strip())
            if result.returncode != 0:
                return {"ok": False, "error": "publish helper failed", "output": "\n".join(output)}

        add_result = _run_repo_cmd(["git", "add", "--", *_publish_scope(slug)])
        if add_result.returncode != 0:
            return {"ok": False, "error": "git add failed", "output": add_result.stdout}

        staged = _run_repo_cmd(["git", "diff", "--cached", "--name-only", "--", *_publish_scope(slug)])
        if staged.returncode != 0:
            return {"ok": False, "error": "git diff failed", "output": staged.stdout}

        committed = False
        if staged.stdout.strip():
            commit = _run_repo_cmd(["git", "commit", "-m", f"Publish {slug} explainer updates"], timeout=120)
            output.append(commit.stdout.strip())
            if commit.returncode != 0:
                return {"ok": False, "error": "git commit failed", "output": "\n".join(output)}
            committed = True

        branch = _git_branch()
        ahead = _git_ahead_count()
        pushed = False
        if committed or ahead > 0:
            push = _run_repo_cmd(["git", "push", "origin", branch], timeout=180)
            output.append(push.stdout.strip())
            if push.returncode != 0:
                return {"ok": False, "error": "git push failed", "output": "\n".join(output)}
            pushed = True

        after = _publish_status_payload(artifact_dir, publishing=False)
        return {
            "ok": True,
            "slug": slug,
            "committed": committed,
            "pushed": pushed,
            "commit": _run_repo_cmd(["git", "rev-parse", "--short", "HEAD"]).stdout.strip(),
            "message": "published and pushed" if pushed else "already up to date",
            "status": after,
            "output": "\n".join(part for part in output if part),
        }
    finally:
        _publish_lock.release()


def _with_charset(content_type: str) -> str:
    """Append `; charset=utf-8` to text-ish content types when missing. Without
    this, browsers fall back to Latin-1 and emojis / non-ASCII glyphs garble."""
    if not content_type:
        return content_type
    needs = (
        content_type.startswith("text/")
        or content_type in ("application/javascript", "application/json", "application/xml")
    )
    if needs and "charset=" not in content_type.lower():
        return f"{content_type}; charset=utf-8"
    return content_type


class FeedbackHandler(http.server.SimpleHTTPRequestHandler):
    feedback_dir: Path = None  # type: ignore
    artifact_dir: Path = None  # type: ignore

    # ---------- override caching: dev server should never cache ----------
    def end_headers(self):
        # Any response is proof of a live client — push the idle deadline back.
        _touch_activity()
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def guess_type(self, path):
        # SimpleHTTPRequestHandler uses this to set Content-Type. Force UTF-8
        # for text/*, JS, JSON so emojis and non-ASCII glyphs render correctly.
        return _with_charset(super().guess_type(path))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/info":
            # Diagnostic endpoint: lets other Claude Code sessions detect what
            # this server is serving so they know whether to reuse or take over.
            info = {
                "artifact_dir": str(self.artifact_dir),
                "feedback_dir": str(self.feedback_dir),
                "lib_dir": str(LIB_DIR),
                "port": self.server.server_address[1],
                "codex_auto_process": _codex_auto_config["enabled"],
            }
            self._json(200, info)
            return
        if parsed.path == "/publish/status":
            try:
                self._json(200, _publish_status_payload(self.artifact_dir))
            except Exception as exc:
                self._json(500, {"ok": False, "error": str(exc)})
            return
        if parsed.path.startswith("/lib/"):
            self._serve_from_lib(parsed.path[len("/lib/"):])
            return
        super().do_GET()

    def _serve_from_lib(self, rel: str):
        # Path-traversal-safe lookup inside LIB_DIR
        try:
            target = (LIB_DIR / rel).resolve()
        except Exception:
            self.send_error(404); return
        if not str(target).startswith(str(LIB_DIR) + os.sep) and target != LIB_DIR:
            self.send_error(403, "forbidden"); return
        if not target.exists() or not target.is_file():
            self.send_error(404); return
        mime, _ = mimetypes.guess_type(str(target))
        if mime is None:
            mime = "application/octet-stream"
        mime = _with_charset(mime)
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/feedback":
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else ""
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._json(400, {"ok": False, "error": "invalid json"})
                return
            data["received_at"] = time.time()
            data["received_iso"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            inbox = self.feedback_dir / "inbox.jsonl"
            with open(inbox, "a") as f:
                f.write(json.dumps(data) + "\n")
            sys.stdout.write(f"[feedback] batch with {len(data.get('comments', []))} comment(s) -> {inbox}\n")
            sys.stdout.flush()
            _trigger_codex_auto_process()
            self._json(200, {"ok": True})
            return

        if parsed.path == "/mark-seen":
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else ""
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
            seen_path = self.feedback_dir / "lastseen.json"
            seen_path.write_text(json.dumps(data, indent=2))
            self._json(200, {"ok": True})
            return

        if parsed.path == "/publish":
            if not _same_origin_or_no_origin(self):
                self._json(403, {"ok": False, "error": "publish is same-origin only"})
                return
            try:
                result = _publish_now(self.artifact_dir)
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}
            self._json(200 if result.get("ok") else 500, result)
            return

        self._json(404, {"ok": False, "error": "unknown endpoint"})

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Silence the default request logging — too noisy for our purposes.
    def log_message(self, format, *args):
        # Only log POSTs and errors
        message = " ".join(map(str, args))
        first = str(args[0]) if args else ""
        if first.startswith("POST") or " 4" in message or " 5" in message:
            sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def _watchdog(idle_timeout_s: int):
    """Daemon thread: terminate the server when (a) the parent process dies,
    or (b) no client has hit us for idle_timeout_s. Polls every 5s. Uses
    os._exit because srv.shutdown() can hang on the per-request thread join
    that ThreadingTCPServer.server_close() does by default — and for a dev
    server graceful close has no upside."""
    watch_parent = (INITIAL_PPID != 1)
    while True:
        time.sleep(5)
        reason = None
        if watch_parent and os.getppid() == 1:
            reason = "parent process exited"
        elif idle_timeout_s > 0 and _idle_seconds() > idle_timeout_s:
            reason = f"idle for >{idle_timeout_s}s with no clients"
        if reason:
            sys.stdout.write(f"[server] {reason}; shutting down\n")
            sys.stdout.flush()
            os._exit(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("artifact_dir", help="directory containing the HTML artifact")
    ap.add_argument("--port", type=int, default=5050)
    ap.add_argument("--idle-timeout", type=int, default=600,
                    help="exit if no client requests for this many seconds (0 = disable). Default 600 (10 min).")
    ap.add_argument("--codex-auto-process", action="store_true",
                    help="run `codex exec` only when new feedback is submitted; avoids idle heartbeat polling.")
    ap.add_argument("--codex-bin", default="codex",
                    help="Codex executable to use with --codex-auto-process. Default: codex.")
    args = ap.parse_args()

    artifact_dir = Path(args.artifact_dir).resolve()
    if not artifact_dir.exists():
        print(f"ERROR: {artifact_dir} does not exist")
        sys.exit(1)

    feedback_dir = artifact_dir / "feedback"
    feedback_dir.mkdir(exist_ok=True)
    inbox = feedback_dir / "inbox.jsonl"
    if not inbox.exists():
        inbox.touch()
    history = feedback_dir / "history.json"
    if not history.exists():
        history.write_text("[]")

    FeedbackHandler.feedback_dir = feedback_dir
    FeedbackHandler.artifact_dir = artifact_dir
    _codex_auto_config["enabled"] = args.codex_auto_process
    _codex_auto_config["codex_bin"] = args.codex_bin
    _codex_auto_config["artifact_dir"] = artifact_dir

    os.chdir(artifact_dir)

    # socketserver.TCPServer doesn't reuse the port quickly enough — subclass:
    class ReuseTCP(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        # Per-request handler threads are daemon so they don't block process
        # exit if a client connection lingers.
        daemon_threads = True

    try:
        srv = ReuseTCP(("", args.port), FeedbackHandler)
    except OSError as e:
        print(f"[server] FATAL: port {args.port} is unavailable ({e}).")
        print(f"[server]  - check what's running there:  curl -s http://localhost:{args.port}/info")
        print(f"[server]  - or kill it:                  lsof -ti:{args.port} | xargs kill")
        print(f"[server]  - or run me on a different port: --port {args.port + 1}")
        sys.exit(1)

    # Auto-shutdown so servers don't accumulate across Claude Code sessions.
    threading.Thread(
        target=_watchdog, args=(args.idle_timeout,), daemon=True
    ).start()

    with srv:
        print(f"[server] serving {artifact_dir}")
        print(f"[server] open http://localhost:{args.port}/")
        print(f"[server] inbox:   {inbox}")
        print(f"[server] history: {history}")
        print(f"[server] info:    http://localhost:{args.port}/info")
        if args.idle_timeout > 0:
            print(f"[server] auto-shutdown: parent-death OR {args.idle_timeout}s idle (no requests). --idle-timeout 0 to disable")
        else:
            print(f"[server] auto-shutdown: parent-death only (idle timeout disabled)")
        if args.codex_auto_process:
            print("[server] codex auto-process: enabled on feedback submit (no idle polling)")
            if _has_unprocessed_feedback(feedback_dir):
                print("[server] codex auto-process: pending feedback found; starting processor")
                _trigger_codex_auto_process()
        print(f"[server] Ctrl-C to stop")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n[server] stopping")


if __name__ == "__main__":
    main()

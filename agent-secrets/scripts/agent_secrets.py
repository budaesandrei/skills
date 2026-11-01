"""agent-secrets: store secrets in the system keyring through a local UI.

Runs on macOS, Windows and Linux desktops.

The secret value only ever travels UI -> this process -> system keyring. Nothing this
tool prints, returns or writes to the registry contains a secret value.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from pathlib import Path

import keyring
import keyring.backends.fail
import keyring.errors

SERVICE = "agent-secrets"
HOME = Path(os.environ.get("AGENT_SECRETS_HOME", Path.home() / ".agent-secrets"))
REGISTRY = HOME / "registry.json"
REQUESTS = HOME / "requests"
HERE = Path(__file__).resolve().parent
UI_TIMEOUT_SECONDS = 600
MAX_FILE_BYTES = 256 * 1024

TYPES = [
    ("api_token", "API key / token", False),
    ("password", "Password", False),
    ("bearer_token", "Bearer token / JWT", False),
    ("oauth_client_secret", "OAuth client secret", False),
    ("oauth_refresh_token", "OAuth refresh token", False),
    ("webhook_secret", "Webhook signing secret", False),
    ("connection_string", "Database / connection string", False),
    ("encryption_key", "Encryption key", False),
    ("totp_seed", "2FA / TOTP seed", False),
    ("ssh_private_key", "SSH private key", True),
    ("private_key", "Private key (PEM)", True),
    ("certificate", "TLS certificate (PEM)", True),
    ("json", "JSON credential / service account", True),
    ("env_file", ".env file", True),
    ("recovery_codes", "Recovery codes", True),
    ("other", "Other", True),
]
ENVS = [("none", "None"), ("local", "Local"), ("dev", "Dev"), ("stg", "Staging"), ("prd", "Production")]
TYPE_IDS = {t[0] for t in TYPES}
ENV_IDS = {e[0] for e in ENVS}
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ENV_VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TEXT_FIELDS = ("description", "provider", "username", "url", "project", "owner", "scopes", "notes")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def account(name: str, env: str) -> str:
    return f"{env}/{name}"


def ensure_home() -> None:
    HOME.mkdir(mode=0o700, parents=True, exist_ok=True)
    REQUESTS.mkdir(mode=0o700, exist_ok=True)


def write_private(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


class locked:
    def __enter__(self):
        ensure_home()
        self.f = open(HOME / ".lock", "a+")
        self.f.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self.f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(self.f, fcntl.LOCK_EX)

    def __exit__(self, *a):
        if os.name == "nt":
            import msvcrt

            self.f.seek(0)
            msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
        self.f.close()


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}


def validate(meta: dict) -> str | None:
    if not NAME_RE.match(meta.get("name", "")):
        return "Name can use letters, numbers, dots, dashes and underscores."
    if meta.get("type") not in TYPE_IDS:
        return "Choose a type."
    if meta.get("env") not in ENV_IDS:
        return "Choose an environment."
    if meta.get("env_var") and not ENV_VAR_RE.match(meta["env_var"]):
        return "Environment variable can only use letters, numbers and underscores."
    if meta.get("expires"):
        try:
            dt.date.fromisoformat(meta["expires"])
        except ValueError:
            return "Expiry must be a valid date."
    if meta.get("rotate_days") not in (None, ""):
        try:
            if int(meta["rotate_days"]) < 1:
                raise ValueError
        except (TypeError, ValueError):
            return "Rotation must be a whole number of days."
    return None


def check_format(kind: str, secret: str) -> str | None:
    if kind == "json":
        try:
            json.loads(secret)
        except ValueError:
            return "That isn't valid JSON."
    if kind in ("certificate", "private_key", "ssh_private_key") and "-----BEGIN " not in secret:
        return "That doesn't look like PEM text (no -----BEGIN line)."
    return None


def public_ref(entry: dict) -> dict:
    """Metadata plus how to reach the value. Never includes the value."""
    acct = entry["keychain_account"]
    return {
        **entry,
        "access": {
            "run_with_secret": f"agent-secrets exec --map {entry['name']}@{entry['env']} -- <command>",
            "keychain_service": SERVICE,
            "keychain_account": acct,
        },
    }


def store(meta: dict, secret: str, replace: bool) -> dict:
    meta = {k: (v.strip() if isinstance(v, str) else v) for k, v in meta.items()}
    err = validate(meta) or check_format(meta["type"], secret)
    if err:
        return {"error": err}
    name, env = meta["name"], meta["env"]
    acct = account(name, env)
    with locked():
        reg = load_registry()
        old = reg.get(acct)
        if old and not replace:
            return {"error": "A secret with this name and environment already exists."}
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        entry = {
            "name": name,
            "env": env,
            "type": meta["type"],
            "tags": tags,
            "expires": None if meta.get("never_expires") else (meta.get("expires") or None),
            "never_expires": bool(meta.get("never_expires")),
            "rotate_days": int(meta["rotate_days"]) if meta.get("rotate_days") else None,
            "env_var": meta.get("env_var") or None,
            "keychain_service": SERVICE,
            "keychain_account": acct,
            "created_at": old["created_at"] if old else now(),
            "updated_at": now(),
        }
        for k in TEXT_FIELDS:
            entry[k] = meta.get(k) or None
        keyring.set_password(SERVICE, acct, secret)
        if keyring.get_password(SERVICE, acct) != secret:
            return {"error": "The system keyring did not save the value correctly."}
        reg[acct] = entry
        write_private(REGISTRY, json.dumps(reg, indent=2, sort_keys=True))
    return {"entry": entry, "replaced": bool(old)}


class Api:
    def __init__(self, prefill: dict):
        self._prefill = prefill
        self._window = None
        self.result = {"status": "cancelled"}

    def config(self):
        return {
            "types": [{"id": i, "label": l, "multiline": m} for i, l, m in TYPES],
            "envs": [{"id": i, "label": l} for i, l in ENVS],
            "prefill": self._prefill,
            "store_name": store_name(),
        }

    def exists(self, name, env):
        return account(name, env) in load_registry()

    def submit(self, meta, secret, replace):
        try:
            r = store(meta, secret, bool(replace))
        except Exception as e:  # noqa: BLE001  shown to the person typing
            return {"error": f"System keyring error: {type(e).__name__}"}
        if "error" in r:
            return r
        self.result = {"status": "stored", "replaced": r["replaced"], "secret": public_ref(r["entry"])}
        self._close(delay=1.1)  # lets the success animation play
        return {"ok": True}

    def cancel(self):
        self.result = {"status": "cancelled"}
        self._close()

    def pick_file(self):
        import webview

        picked = self._window.create_file_dialog(webview.FileDialog.OPEN)
        if not picked:
            return None
        p = Path(picked[0])
        if p.stat().st_size > MAX_FILE_BYTES:
            return {"error": "That file is too large to be a credential."}
        try:
            return {"name": p.name, "text": p.read_text()}
        except UnicodeDecodeError:
            return {"error": "Only text files can be loaded."}

    def _close(self, delay: float = 0):
        t = threading.Timer(delay, self._window.destroy)
        t.daemon = True
        t.start()


def run_ui(prefill: dict) -> dict:
    import webview

    api = Api(prefill)
    window = webview.create_window(
        "Store secret",
        html=(HERE / "ui.html").read_text(),
        js_api=api,
        width=560,
        height=720,
        min_size=(460, 520),
        on_top=True,
    )
    api._window = window

    def on_ready():
        if sys.platform == "darwin":
            from AppKit import NSApplication
            from PyObjCTools import AppHelper

            AppHelper.callAfter(lambda: NSApplication.sharedApplication().activateIgnoringOtherApps_(True))

        def expire():
            api.result = {"status": "timeout"}
            api._close()

        t = threading.Timer(UI_TIMEOUT_SECONDS, expire)
        t.daemon = True
        t.start()

    webview.start(on_ready, private_mode=True)
    return api.result


def store_name() -> str:
    return {"darwin": "macOS Keychain", "win32": "Windows Credential Manager"}.get(sys.platform, "system keyring")


def unavailable_reason() -> str | None:
    """Why this machine can't take a secret, for example a server with no screen."""
    if sys.platform == "linux" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return "No graphical display, so the input window can't open."
    backend = keyring.get_keyring()
    if type(backend).__module__.rsplit(".", 1)[-1] in ("fail", "null") or isinstance(backend, keyring.backends.fail.Keyring):
        return "No system keyring is available. On Linux, install and unlock GNOME Keyring or KWallet."
    return None


def prefill_from(args) -> dict:
    p = json.loads(args.prefill) if args.prefill else {}
    if not isinstance(p, dict):
        raise SystemExit("--prefill must be a JSON object")
    allowed = {"name", "type", "env", "expires", "never_expires", "env_var", "rotate_days", "tags", *TEXT_FIELDS}
    unknown = set(p) - allowed
    if unknown:
        raise SystemExit(f"Unknown prefill fields: {sorted(unknown)}")
    if isinstance(p.get("tags"), list):
        p["tags"] = ", ".join(p["tags"])
    return p


def cmd_prompt(args) -> int:
    ensure_home()
    reason = unavailable_reason()
    res = {"status": "unavailable", "reason": reason} if reason else run_ui(prefill_from(args))
    text = json.dumps(res, indent=2)
    if args.request_file:
        write_private(Path(args.request_file), text)
    print(text, flush=True)
    sys.stderr.flush()
    os._exit({"stored": 0, "unavailable": 4}.get(res["status"], 3))  # GUI threads must not delay the callback


def warnings(e: dict) -> list:
    out = []
    if e.get("expires"):
        days = (dt.date.fromisoformat(e["expires"]) - dt.date.today()).days
        if days < 0:
            out.append(f"expired {-days} days ago")
        elif days <= 14:
            out.append(f"expires in {days} days")
    return out


def cmd_list(args) -> int:
    rows = list(load_registry().values())
    if args.env:
        rows = [r for r in rows if r["env"] == args.env]
    print(json.dumps([{**public_ref(r), "warnings": warnings(r)} for r in rows], indent=2))
    return 0


def find(reg: dict, spec: str) -> dict:
    name, _, env = spec.partition("@")
    hits = [e for e in reg.values() if e["name"] == name and (not env or e["env"] == env)]
    if len(hits) != 1:
        where = ", ".join(e["env"] for e in hits)
        raise SystemExit(f"{spec}: " + (f"matches several environments ({where}); use name@env" if hits else "not found"))
    return hits[0]


def cmd_exec(args) -> int:
    reg = load_registry()
    env = dict(os.environ)
    for m in args.map:
        var, _, spec = m.rpartition("=")
        e = find(reg, spec)
        var = var or e.get("env_var")
        if not var or not ENV_VAR_RE.match(var):
            raise SystemExit(f"{spec}: no environment variable set; use VAR={spec}")
        for w in warnings(e):
            print(f"agent-secrets: warning: {spec} {w}", file=sys.stderr)
        value = keyring.get_password(SERVICE, e["keychain_account"])
        if value is None:
            raise SystemExit(f"{spec}: missing from the system keyring")
        env[var] = value
    cmd = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not cmd:
        raise SystemExit("exec needs a command after --")
    return subprocess.run(cmd, env=env).returncode


def clipboard_mac(value: str, seconds: int) -> None:
    import time

    from AppKit import NSPasteboard, NSPasteboardTypeString

    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.setString_forType_(value, NSPasteboardTypeString)
    for marker in ("org.nspasteboard.ConcealedType", "org.nspasteboard.TransientType", "com.apple.is-remote-clipboard.disabled"):
        pb.setString_forType_("", marker)
    mark = pb.changeCount()
    print(json.dumps({"status": "copied", "seconds": seconds}), flush=True)
    time.sleep(seconds)
    if pb.changeCount() == mark:
        pb.clearContents()


def clipboard_command() -> list[str]:
    if sys.platform == "win32":
        return ["clip"]
    for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
        if shutil.which(cmd[0]):
            return cmd
    raise SystemExit("No clipboard tool found. Install wl-clipboard or xclip.")


def clipboard_other(value: str, seconds: int) -> None:
    import time

    cmd = clipboard_command()
    encoding = "utf-16-le" if sys.platform == "win32" else "utf-8"
    subprocess.run(cmd, input=value.encode(encoding), check=True, shell=sys.platform == "win32")
    print(json.dumps({"status": "copied", "seconds": seconds}), flush=True)
    time.sleep(seconds)
    subprocess.run(cmd, input=b"", check=True, shell=sys.platform == "win32")


def cmd_copy(args) -> int:
    """Clipboard hand-off for apps that can't read the keyring. Never prints the value."""
    e = find(load_registry(), args.spec)
    value = keyring.get_password(SERVICE, e["keychain_account"])
    if value is None:
        raise SystemExit(f"{args.spec}: missing from the system keyring")
    (clipboard_mac if sys.platform == "darwin" else clipboard_other)(value, args.seconds)
    print(json.dumps({"status": "cleared"}), flush=True)
    return 0


def desktop_config_path() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if sys.platform == "win32":
        return Path(os.environ["APPDATA"]) / "Claude/claude_desktop_config.json"
    return Path.home() / ".config/Claude/claude_desktop_config.json"


def cmd_connect_desktop(args) -> int:
    """Register the connector with Claude Desktop, keeping any existing settings."""
    path = desktop_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(path.read_text()) if path.exists() else {}
    cfg.setdefault("mcpServers", {})[SERVICE] = {"command": sys.executable, "args": [str(HERE / "mcp_server.py")]}
    write_private(path, json.dumps(cfg, indent=2))
    print(json.dumps({"status": "connected", "config": str(path), "next": "Restart Claude Desktop"}))
    return 0


def cmd_doctor(args) -> int:
    print(json.dumps({"platform": sys.platform, "store": store_name(), "backend": type(keyring.get_keyring()).__module__, "ready": unavailable_reason() is None, "reason": unavailable_reason()}, indent=2))
    return 0


def cmd_delete(args) -> int:
    with locked():
        reg = load_registry()
        e = find(reg, args.spec)
        try:
            keyring.delete_password(SERVICE, e["keychain_account"])
        except keyring.errors.PasswordDeleteError:
            pass
        del reg[e["keychain_account"]]
        write_private(REGISTRY, json.dumps(reg, indent=2, sort_keys=True))
    print(json.dumps({"status": "deleted", "name": e["name"], "env": e["env"]}))
    return 0


# Used by the Claude Desktop connector, where a blocking call could time out.
def start_request(prefill: dict) -> str:
    ensure_home()
    rid = uuid.uuid4().hex
    argv = [sys.executable, str(Path(__file__).resolve()), "prompt", "--request-file", str(REQUESTS / f"{rid}.json")]
    if prefill:
        argv += ["--prefill", json.dumps(prefill)]
    subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return rid


def read_request(rid: str) -> dict | None:
    if not re.fullmatch(r"[0-9a-f]{32}", rid):
        return {"status": "unknown_request"}
    p = REQUESTS / f"{rid}.json"
    return json.loads(p.read_text()) if p.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser(prog="agent-secrets")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt", help="open the input window and wait")
    p.add_argument("--prefill", help="JSON object of metadata; never a secret value")
    p.add_argument("--request-file", help=argparse.SUPPRESS)
    p.set_defaults(fn=cmd_prompt)
    p = sub.add_parser("list", help="show metadata for stored secrets")
    p.add_argument("--env", choices=sorted(ENV_IDS))
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("exec", help="run a command with secrets as environment variables")
    p.add_argument("--map", action="append", required=True, metavar="[VAR=]NAME[@ENV]")
    p.add_argument("command", nargs=argparse.REMAINDER)
    p.set_defaults(fn=cmd_exec)
    p = sub.add_parser("copy", help="put a secret on the clipboard briefly, for the person to paste")
    p.add_argument("spec", metavar="NAME[@ENV]")
    p.add_argument("--seconds", type=int, default=45)
    p.set_defaults(fn=cmd_copy)
    p = sub.add_parser("connect-desktop", help="register with Claude Desktop")
    p.set_defaults(fn=cmd_connect_desktop)
    p = sub.add_parser("doctor", help="check this machine can run agent-secrets")
    p.set_defaults(fn=cmd_doctor)
    p = sub.add_parser("delete", help="remove a secret and its metadata")
    p.add_argument("spec", metavar="NAME[@ENV]")
    p.set_defaults(fn=cmd_delete)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

"""Switch's authenticated WebSocket events feed one serial worker across all rooms."""
import argparse
import asyncio
import fcntl
import json
import os
import signal
import sys
import tempfile
import urllib.parse
import urllib.request
import uuid

from .ai import AgentModel
from .config import DATA, read_json
from .exchange import Exchange
from .render import render
from .state import State
from .worker import Worker


def safe_url(value):
    url = urllib.parse.urlsplit(value)
    if (not url.hostname or url.username or url.password or url.query or url.fragment
            or (url.scheme != "https" and not (url.scheme == "http" and url.hostname in ("127.0.0.1", "localhost")))):
        raise ValueError("Switch URL must use HTTPS (HTTP is allowed only on loopback)")
    return value.rstrip("/")


def write_private(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def post(url, key, payload):
    request = urllib.request.Request(url, json.dumps(payload).encode(),
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(100000)
            return json.loads(body) if body else {}
    except (OSError, ValueError) as exc:
        raise RuntimeError("Switch request failed; check connectivity, permissions and server configuration") from exc


def message_event(frame):
    if frame.get("event") != "message":
        return None
    data = frame.get("data", {})
    # All messages are delivered; the worker decides (listen-mode evidence vs addressed commands).
    return data if isinstance(data.get("payload"), dict) else None


def chunks(result):
    content = render(result)
    return [content[start:start + 3500] for start in range(0, len(content), 3500)]


class ProtocolError(RuntimeError):
    pass


async def serve(worker, identity, checkpoint):
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed

    task = asyncio.current_task()
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, task.cancel)

    base = safe_url(identity["url"])
    agent = urllib.parse.quote(identity["id"], safe="")
    endpoint = base.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
    progress = read_json(checkpoint) if checkpoint.exists() else {"cursor": None, "generation": None}
    queue = asyncio.Queue(maxsize=32)

    async def consume():
        while True:
            frame = await queue.get()
            sequence = int(frame["id"])
            try:
                if progress["cursor"] is not None and sequence <= progress["cursor"]:
                    continue
                event = message_event(frame)
                print(f"frame {frame.get('event')} seq={sequence} routed={bool(event)}"
                      + (f" addressed={event['payload'].get('addressed')} room=..{str(event.get('room_id'))[-6:]}" if event else ""),
                      file=sys.stderr, flush=True)
                if event:
                    spoken = event["payload"].get("addressed") is True  # never reply to unaddressed chatter
                    try:
                        if await asyncio.to_thread(worker.is_slow, event):
                            await asyncio.to_thread(post, f"{base}/agents/{agent}/message", identity["api_key"],
                                                    {"room_id": event["room_id"], "content": "⏳ Working on it… this can take up to a minute."})
                    except Exception:
                        pass  # the acknowledgement is a courtesy; the real work still runs
                    try:
                        result = await asyncio.to_thread(worker.handle, event)
                    except ValueError as exc:
                        result = {"reply": f"Request rejected: {exc}"} if spoken else None
                    except Exception:
                        # Do not echo exception bodies: they may contain provider or private data.
                        result = {"reply": "Request failed. Check operator logs/configuration and retry. No failed brief was charged."} if spoken else None
                    if result is not None:
                        for content in chunks(result):
                            # Retry forwarding independently; do not regenerate or charge again.
                            for attempt in range(4):
                                try:
                                    await asyncio.to_thread(post, f"{base}/agents/{agent}/message", identity["api_key"],
                                                            {"room_id": event["room_id"], "content": content})
                                    break
                                except RuntimeError:
                                    if attempt == 3:
                                        raise ProtocolError("Reply delivery failed; restart to retry from persisted cursor")
                                    await asyncio.sleep(2 ** attempt)
                progress["cursor"] = sequence
                write_private(checkpoint, progress)
            finally:
                queue.task_done()

    async def receive():
        failures = 0
        while True:
            params = {"connection_id": identity["connection_id"], "scope": "all", "filter": "all",
                      "start_from": "head" if progress["cursor"] is None else str(progress["cursor"]),
                      "client": "commongrown", "client_version": "0.1.0"}
            if progress["generation"] is not None:
                params["expected_generation"] = str(progress["generation"])
            try:
                async with connect(f"{endpoint}/agents/{agent}/connection/ws?{urllib.parse.urlencode(params)}",
                                   additional_headers={"Authorization": f"Bearer {identity['api_key']}"},
                                   open_timeout=20, max_size=1000000) as socket:
                    failures = 0
                    async for raw in socket:
                        frame = json.loads(raw)
                        kind = frame.get("event", frame.get("type"))
                        data = frame.get("data", frame)
                        if kind == "connection_state":
                            if data.get("agent_id") != identity["id"]:
                                raise ProtocolError("Unexpected Switch agent identity")
                            progress["generation"] = data["generation"]
                            if progress["cursor"] is None:
                                progress["cursor"] = data["cursor"]
                            elif data["cursor"] > progress["cursor"]:
                                raise ProtocolError("Switch cursor advanced past locally completed work; operator reconciliation required")
                            write_private(checkpoint, progress)
                        elif kind == "ping":
                            await socket.send(json.dumps({"type": "pong", "cursor": progress["cursor"]}))
                        elif kind in ("gap", "replaced", "revoked", "error"):
                            raise ProtocolError("Switch connection needs operator reconciliation; refusing to skip events")
                        elif "id" in frame:
                            await queue.put(frame)
            except (OSError, ConnectionClosed) as exc:
                failures += 1
                print(f"Switch connection lost ({type(exc).__name__}); retry {failures}", file=sys.stderr, flush=True)
                await asyncio.sleep(min(30, 2 ** min(failures, 5)))

    consumer = asyncio.create_task(consume())
    receiver = asyncio.create_task(receive())
    try:
        done, _ = await asyncio.wait((consumer, receiver), return_when=asyncio.FIRST_EXCEPTION)
        for task in done:
            task.result()
    finally:
        consumer.cancel()
        receiver.cancel()
        await asyncio.gather(consumer, receiver, return_exceptions=True)


def main():
    parser = argparse.ArgumentParser(description="One CommonGrown worker for company-isolated Switch rooms")
    parser.add_argument("action", choices=("register", "run"))
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    identity_path = DATA / "switch-identity.json"
    try:
        config = read_json(args.config)
        url = safe_url(config["url"])
        if args.action == "register":
            if identity_path.exists():
                raise ValueError("Agent identity already exists; registration is a one-time operation")
            registration = os.environ.get("SWITCH_REGISTRATION_KEY")
            if not registration:
                raise ValueError("Set SWITCH_REGISTRATION_KEY for one-time registration")
            identity = post(f"{url}/agents", registration, {
                "name": config.get("name", "commongrown"), "description": "Company-isolated B2B opportunity assistant",
                "connector_type": "commongrown-python", "integration_profile": {
                    "connection_model": "always_on", "message_exchange": True,
                    "pre_invocation_mediation": [], "post_invocation_mediation": [], "event_reporting": []}})
            if not identity.get("id") or not identity.get("api_key"):
                raise ValueError("Switch registration returned no identity")
            write_private(identity_path, identity | {"url": url, "connection_id": str(uuid.uuid4())})
            print("Registered. Identity saved privately; configure room membership and allowed senders in Switch.")
            return 0
        identity = read_json(identity_path)
        if identity["url"] != url:
            raise ValueError("Configuration server differs from registered identity")
        DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (DATA / "worker.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = State(DATA / "accounts.db")
            worker = Worker(state, Exchange.open(DATA / "chroma"), AgentModel(), config, DATA)
            asyncio.run(serve(worker, identity, DATA / "switch-checkpoint.json"))
        return 0
    except asyncio.CancelledError:
        return 0
    except ProtocolError as exc:
        print(str(exc), file=sys.stderr)
        return 78
    except (ValueError, OSError, KeyError, RuntimeError):
        print("Worker setup failed. Check configuration, seed data, model credentials and Switch identity.", file=sys.stderr)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())

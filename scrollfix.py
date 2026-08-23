#!/usr/bin/env python3
"""Background daemon: makes Family7's page actually scroll.

Root cause (confirmed live via Chrome DevTools Protocol on the TV): Family7's
page has real CSS overflow set up correctly, but the webOS/Chromium
compositor decides up front that nothing on the page is scrollable, so real
remote-wheel events arrive as isTrusted:true / cancelable:false and never
move scrollTop -- no CSS or default-action trick can change that.

Fix: attach our own 'wheel' listener (listening, not preventing default) and
manually move document.scrollingElement.scrollTop by the event's deltaY.
That's a separate, explicit scroll action -- confirmed working live.

Since this app's index.html does a one-time top-level navigation to
family7.nl (not an iframe), our own JS context is destroyed on navigation,
so the listener can't just live in index.html. Instead this daemon runs as
a background root process, polls the on-device Chrome DevTools Protocol
endpoint (127.0.0.1:9998) for this app's WAM tab, and keeps a live debugger
connection open so the fix re-applies to every new document that tab loads.
"""

import base64
import hashlib
import json
import socket
import threading
import time
import urllib.request

CDP_HOST = "127.0.0.1"
CDP_PORT = 9998
APP_DESCRIPTION = "nl.arnolderuiter.family7"
POLL_INTERVAL_SECONDS = 3
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

FIX_JS = """
(function(){
  if (window.__scrollFixInstalled) return;
  window.__scrollFixInstalled = true;
  window.addEventListener('wheel', function(e){
    if (document.scrollingElement) {
      document.scrollingElement.scrollTop += e.deltaY;
    }
  }, {capture: true, passive: true});
})();
"""

tracked_target_ids = set()
tracked_lock = threading.Lock()


def _handshake(sock, host, port, path):
    key = base64.b64encode(_urandom(16)).decode("ascii")
    lines = [
        "GET %s HTTP/1.1" % path,
        "Host: %s:%d" % (host, port),
        "Upgrade: websocket",
        "Connection: Upgrade",
        "Sec-WebSocket-Key: %s" % key,
        "Sec-WebSocket-Version: 13",
        "",
        "",
    ]
    sock.sendall("\r\n".join(lines).encode("ascii"))
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            raise OSError("connection closed during handshake")
        buf += chunk
    header = buf.split(b"\r\n\r\n", 1)[0].decode("latin-1")
    status_line = header.split("\r\n", 1)[0]
    if " 101 " not in (" " + status_line + " "):
        raise OSError("unexpected handshake response: %s" % status_line)


def _urandom(n):
    import os

    return os.urandom(n)


def _send_frame(sock, payload):
    data = payload.encode("utf-8")
    header = bytearray([0x80 | 0x1])
    length = len(data)
    mask = _urandom(4)
    if length <= 125:
        header.append(0x80 | length)
    elif length <= 0xFFFF:
        header.append(0x80 | 126)
        header += length.to_bytes(2, "big")
    else:
        header.append(0x80 | 127)
        header += length.to_bytes(8, "big")
    header += mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    sock.sendall(bytes(header) + masked)


def _recv_frame(sock):
    def recv_exact(n):
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise OSError("connection closed")
            buf += chunk
        return buf

    first2 = recv_exact(2)
    opcode = first2[0] & 0x0F
    length = first2[1] & 0x7F
    if length == 126:
        length = int.from_bytes(recv_exact(2), "big")
    elif length == 127:
        length = int.from_bytes(recv_exact(8), "big")
    payload = recv_exact(length) if length else b""
    return opcode, payload


def _watch_target(target):
    target_id = target["id"]
    ws_url = target["webSocketDebuggerUrl"]
    path = ws_url.split(CDP_HOST + ":" + str(CDP_PORT), 1)[1]
    sock = socket.create_connection((CDP_HOST, CDP_PORT), timeout=10)
    try:
        _handshake(sock, CDP_HOST, CDP_PORT, path)
        msg_id = 1
        _send_frame(sock, json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        _send_frame(
            sock,
            json.dumps(
                {
                    "id": msg_id,
                    "method": "Page.addScriptToEvaluateOnNewDocument",
                    "params": {"source": FIX_JS},
                }
            ),
        )
        msg_id += 1
        _send_frame(
            sock,
            json.dumps(
                {"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": FIX_JS}}
            ),
        )
        print("scrollfix: injected into target %s" % target_id, flush=True)
        sock.settimeout(60)
        while True:
            try:
                opcode, _payload = _recv_frame(sock)
            except socket.timeout:
                continue
            if opcode == 0x8:
                break
    except OSError as exc:
        print("scrollfix: target %s connection ended: %s" % (target_id, exc), flush=True)
    finally:
        try:
            sock.close()
        except OSError:
            pass
        with tracked_lock:
            tracked_target_ids.discard(target_id)


def main():
    print("scrollfix: watching for %s" % APP_DESCRIPTION, flush=True)
    while True:
        try:
            with urllib.request.urlopen(
                "http://%s:%d/json" % (CDP_HOST, CDP_PORT), timeout=5
            ) as resp:
                targets = json.loads(resp.read().decode("utf-8"))
        except OSError:
            targets = []
        for target in targets:
            if target.get("description") != APP_DESCRIPTION:
                continue
            target_id = target["id"]
            with tracked_lock:
                if target_id in tracked_target_ids:
                    continue
                tracked_target_ids.add(target_id)
            threading.Thread(target=_watch_target, args=(target,), daemon=True).start()
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

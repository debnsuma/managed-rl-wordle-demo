"""Optional: play any word live on Crusoe Managed RL, for a staffed moment at the booth.

Opens one sampling-only session serving the base model and the trained adapter, then answers

    POST /play   {"word": "crane"}   ->  {"base": game, "rl": game}      (both play the word)
    GET  /health                     ->  {"ok": true, "session": "msess_..."}

on http://127.0.0.1:8765. Needs the Wordle recipe installed (the environment and rollout code),
a key with Managed RL access in CRUSOE_API_KEY, and network. Keep this process alive all day;
the session is released when it exits.

    cd <developer hub>/examples/training/crusoe-mill-annotated/wordle
    uv run python <this folder>/live_server.py --checkpoint mill://.../qwen3.8-27b-grpo --model Qwen/Qwen3.8-27B
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv

from wordle import rollout
from wordle.mill import open_session, sampler_for
from wordle.words import is_valid_guess


def main():
    load_dotenv()
    os.environ.setdefault("CRUSOE_BASE_URL", "https://api.intelligence.crusoecloud.com")
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True, help="mill:// path of the trained adapter")
    p.add_argument("--model", default="Qwen/Qwen3.8-27B")
    p.add_argument("--port", type=int, default=8765)
    a = p.parse_args()

    client, _, tok, types = open_session(a.model, train=False)
    samplers = {"base": sampler_for(client, a.model, None), "rl": sampler_for(client, a.model, a.checkpoint)}
    sp = types.SamplingParams(max_tokens=1536, temperature=1.0, top_p=0.95, top_k=20)

    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def do_OPTIONS(self): self._send(200, {})

        def do_GET(self):
            self._send(200, {"ok": True, "session": client.session_id, "model": a.model} if self.path == "/health" else {"error": "not found"})

        def do_POST(self):
            if self.path != "/play": return self._send(404, {"error": "not found"})
            n = int(self.headers.get("Content-Length", 0)); word = (json.loads(self.rfile.read(n) or b"{}").get("word") or "").strip().lower()
            if len(word) != 5 or not is_valid_guess(word): return self._send(400, {"error": "give a five-letter dictionary word"})
            out = {}
            for name, s in samplers.items():
                g = rollout.play_batch(s, tok, types, [word], sp, 8192)[0]
                out[name] = {"board": g.board, "reason": g.reason, "won": g.won, "texts": g.texts}
            self._send(200, out)

        def log_message(self, *args): pass

    print(f"live on http://127.0.0.1:{a.port}  session {client.session_id}  Ctrl-C to release it", flush=True)
    try:
        HTTPServer(("127.0.0.1", a.port), H).serve_forever()
    finally:
        client.close(); print("session closed")


if __name__ == "__main__":
    main()

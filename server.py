#!/usr/bin/env python3
"""最小の stdio MCP サーバー（名前は docs）。

Skills extension（io.modelcontextprotocol/skills, SEP-2640）を手書きの JSON-RPC で実装する。
- capabilities に resources と extensions["io.modelcontextprotocol/skills"] を宣言
- skills/list・skills/get でスキルの目録（frontmatter と、ファイルの digest・size）を返す
- resources/read で SKILL.md の中身を返す
道具は1つ（word_count：文字数を数えるだけ）。外部コマンドは何も走らせない。
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent / "skills"
EXT = "io.modelcontextprotocol/skills"
CACHE = {"ttlMs": 300000, "cacheScope": "public"}
LOG = None  # デバッグ用に path を入れると受信を書き出す


def log(msg):
    if LOG:
        with open(LOG, "a") as f:
            f.write(msg + "\n")


def parse_frontmatter(text):
    fm = {}
    if text.startswith("---\n"):
        head = text[4:].split("\n---\n", 1)[0]
        for line in head.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    return fm


def skill_entries():
    out = []
    for d in sorted(p for p in ROOT.iterdir() if (p / "SKILL.md").is_file()):
        files = sorted(f for f in d.rglob("*") if f.is_file())
        manifest = []
        for f in files:
            b = f.read_bytes()
            manifest.append({
                "uri": f"skill://{d.name}/{f.relative_to(d).as_posix()}",
                "digest": "sha256:" + hashlib.sha256(b).hexdigest(),
                "size": len(b),
            })
        fm = parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
        out.append({"uri": f"skill://{d.name}/SKILL.md", "frontmatter": fm, "resources": manifest})
    return out


def capabilities():
    return {"tools": {}, "resources": {}, "extensions": {EXT: {}}}


def handle(method, params):
    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": capabilities(),
            "serverInfo": {"name": "docs", "version": "0.1.0"},
        }
    if method == "server/discover":
        return {
            "resultType": "complete",
            "supportedVersions": ["2026-07-28"],
            "capabilities": capabilities(),
            "_meta": {"io.modelcontextprotocol/serverInfo": {"name": "docs", "version": "0.1.0"}},
            **CACHE,
        }
    if method == "ping":
        return {}
    if method == "skills/list":
        return {"resultType": "complete", "skills": skill_entries(), **CACHE}
    if method == "skills/get":
        for e in skill_entries():
            if e["uri"] == params.get("uri"):
                return {"resultType": "complete", "skill": e, **CACHE}
        raise LookupError(params.get("uri"))
    if method == "resources/list":
        return {"resultType": "complete", "resources": [], **CACHE}
    if method == "resources/templates/list":
        return {"resultType": "complete", "resourceTemplates": [], **CACHE}
    if method == "resources/read":
        uri = params.get("uri", "")
        if uri.startswith("skill://"):
            p = (ROOT / uri[len("skill://"):]).resolve()
            if ROOT in p.parents and p.is_file():
                return {"resultType": "complete", "contents": [
                    {"uri": uri, "mimeType": "text/markdown", "text": p.read_text(encoding="utf-8")}
                ], **CACHE}
        raise LookupError(uri)
    if method == "tools/list":
        return {"resultType": "complete", **CACHE, "tools": [{
            "name": "word_count",
            "description": "文章の文字数を数える。",
            "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        }]}
    if method == "tools/call":
        text = (params.get("arguments") or {}).get("text", "")
        return {"resultType": "complete", "content": [{"type": "text", "text": f"{len(text)} 文字"}]}
    if method == "prompts/list":
        return {"resultType": "complete", "prompts": [], **CACHE}
    raise NotImplementedError(method)


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        log("<- " + line)
        if "id" not in msg:  # 通知（notifications/initialized など）
            continue
        try:
            resp = {"jsonrpc": "2.0", "id": msg["id"], "result": handle(msg.get("method"), msg.get("params") or {})}
        except LookupError as e:
            resp = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32602, "message": f"unknown: {e}"}}
        except NotImplementedError as e:
            resp = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": f"method not found: {e}"}}
        out = json.dumps(resp, ensure_ascii=False)
        log("-> " + out)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        LOG = sys.argv[1]
    main()

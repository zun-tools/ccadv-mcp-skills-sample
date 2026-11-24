# ccadv-mcp-skills-sample

YouTube チャンネル「ずんだもんの実験道具箱」の Claude Code 講座 ccadv「MCP サーバーの skill」の回で使った再現サンプルです。

動画: （公開後に追記します）

## 何のサンプルか

ツール（文字数を数える）1つと、skill（手順書）3つを配る最小の MCP サーバー「docs」（`server.py`）と、その登録（`.mcp.json`）です。
MCP の Skills extension に対応していて、Claude Code のプロンプトで `/docs:` と打つと、サーバーが配る skill が並びます。

| skill | 中身 |
|---|---|
| `/docs:pdf` | PDF の資料を読んで、要点を3行にまとめる手順 |
| `/docs:style` | 文章をチームの文体（です・ます、短い文）にそろえる手順 |
| `/docs:release-notes` | 変更点の一覧から、利用者向けの告知文を作る手順 |

手順書の本文は `skills/<名前>/SKILL.md` にあります。仕組みを見るための小さなサーバーで、手順書の中身は見本です。

## 必要なもの

- 新しめの Claude Code（CLI）。MCP サーバーの skill は公開ベータの機能です。使える条件（版・プラン・使えない環境）は公式の [Use skills from MCP servers](https://code.claude.com/docs/en/mcp) を見てください
- Python 3（標準ライブラリだけで動きます。追加のインストールはありません）

## 動かし方

```bash
git clone https://github.com/zun-tools/ccadv-mcp-skills-sample.git
cd ccadv-mcp-skills-sample
claude
```

1. 初回は「New MCP server found in this project: docs」と出るので、使う側（Use this MCP server）を選びます
2. プロンプトで `/docs:` と打つと、3つの skill が並びます（`/docs` だけだと、別の名前の skill と混ざることがあります）
3. `/skills` を開いて `docs:` で絞ると、手元の skill と並んで `mcp` の印つきで見えます

## 自分のサーバーで skill を配るには

`server.py` を見本にしてください。要点は次のとおりです。

- capabilities に `resources` と `extensions["io.modelcontextprotocol/skills"]` を出す
- `skills/list` で目録（`skill://<名前>/SKILL.md` の uri・frontmatter・各ファイルの digest）を返し、本文は `resources/read` で配る
- この拡張は MCP のプロトコル版 2026-07-28 以降が前提です。`server/discover` に新しい版を返さないと、Claude Code は古い接続に戻り、skill は出ません

仕様: [Skills extension（modelcontextprotocol.io）](https://modelcontextprotocol.io/extensions/skills/overview)

## 注意

- skill は Claude にコードを走らせる指示を含められ、サーバーはいつでも中身を変えられます。つなぐのは信頼できるサーバーだけにしてください
- `python3 server.py <パス>` と起動すると、そのパスへ通信の記録を書きます（既定では書きません）
- 動画と同じ中身を保つため、サンプル自体は改変しません

## ファイル

- `server.py` — MCP サーバー本体（標準ライブラリのみ・Skills extension 対応）
- `.mcp.json` — プロジェクト用の登録（`docs` → `python3 server.py`）
- `skills/` — 配る手順書3つ
- `LICENSE` — MIT

## TODO-015. ruff の規則を増やす

モデル / effort: Sonnet / low

### きっかけ

`pyproject.toml` に ruff の設定が無く、既定の `E4` / `E7` / `E9` / `F`
だけで動いていた。import の順（`I`）などは見ていなかった。

`line-length` も既定の 88 のままだったが、実際のコードは 79 で折り返して
いた。

### やったこと

- `[tool.ruff]` に `line-length = 79` を足した
- `[tool.ruff.lint]` の `select` に `I` / `B` / `UP` を足した
  （既定の `E4` / `E7` / `E9` / `F` に追加）
- 指摘された5件を `ruff check --fix` で直した（import の並び替えが
  4件、`UP037`（型注釈の不要な引用符除去）が1件）

### テスト

`uv run pytest` / `uv run ruff check src/ tests/` / `uv run mypy src/ tests/` /
`uv run basedpyright` を実行し、いずれもエラー・警告0、テスト全成功。

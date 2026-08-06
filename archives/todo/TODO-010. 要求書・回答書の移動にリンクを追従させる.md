# TODO-010. 要求書・回答書の移動にリンクを追従させる

## きっかけ

要求書 2 通・回答書 2 通（`20260806a`〜`20260806d`）を `docs/` から
`archives/` へ移した。これらは現行の仕様書ではなく、やり取りの記録なので
`archives/` が置き場所として正しい。ただし、それらを指している他の
文書・コードのパスが `docs/...` のまま残っていた。

## やったこと

`docs/20260806` を `archives/20260806` に置き換えた。

- `archives/todo/TODO-001. ytstreetorgan からの改善要求への対応.md`
- `archives/todo/TODO-002. 改善要求への回答書を作成する.md`
- `archives/todo/TODO-003. MIDI ファイルの移調（要求書 2 通目）.md`
- `archives/todo/TODO-004. 要求書 2 通目への回答書を作成する.md`
- `archives/todo/TODO-007. my_logger.py を廃止して mylog.py へ切り替える.md`
- `tests/test_midi_writer.py`（docstring）

移した 4 つのファイルが互いに張っている相対リンクは、4 つとも同じ
ディレクトリへ一緒に移動したので、直す必要は無かった。

## テスト

`pytest` / `ruff` / `mypy` / `basedpyright` の 4 つとも通した
（108 passed、エラー 0・警告 0）。変更は docstring とドキュメントだけなので
挙動は変わらない。

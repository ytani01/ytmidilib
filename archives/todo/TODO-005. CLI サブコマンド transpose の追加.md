# TODO-005. CLI サブコマンド `transpose` の追加

## きっかけ

要求書には無い、こちら側の追加。**[[TODO-003]] の完了後に行う**
（`transpose_file()` の薄いラッパーなので、先に本体が要る）。

```
ytmidilib transpose SRC DST N [--clip] [--drums] [-d]
```

## やったこと

- `__main__.py` に `TransposeApp` を追加し、他のサブコマンドに合わせて
  `main()` → `finally: end()` の形で呼ぶ
- 引数・オプションは `transpose_file()` に 1 対 1 で対応させる。
  `--clip` / `-c`、`--drums` / `-D`（既定 off ＝ ライブラリ側の既定と同じ）
- `N` が負の値（`-2` など）でもオプションと誤解されないようにする。
  このコマンドだけ `ignore_unknown_options=True`
  （`TRANSPOSE_CONTEXT_SETTINGS`）
- 範囲外の `ValueError` は `click.ClickException` に包み、
  `.. use --clip` を添えて 1 行で出す（トレースバックを出さない）

## テスト

当時は手動確認。後に [[TODO-006]] で `tests/test_cli.py` に残した。

- `ytmidilib transpose a.mid b.mid 2` で移調できる
- `ytmidilib transpose a.mid b.mid -2` が通る（負の値）
- `--clip` 無しで範囲外なら、エラーが分かる形で表示される。
  `Error: note out of range: 60 + 100 = 160 (channel:0) .. use --clip`
  （終了コード 1）
- `-h` のヘルプが他のサブコマンドと同じ体裁
- lint / 型チェック 3 種がエラー 0・警告 0

完了条件:

- CLI から移調できる — 完了
- `ytmidilib -h` に `transpose` が出る — 完了

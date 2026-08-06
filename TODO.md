# TODO

**残っている項目: TODO-007。** これまでに 6 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-008` から。**

---

## TODO-007. `my_logger.py` を廃止して `mylog.py`（loguru）へ切り替える

- [ ] `pyproject.toml` の依存に `loguru` を足す（`uv add loguru`）
- [ ] 各モジュールを `from loguru import logger` に切り替える
      （`self._log` と module 直下の `LOG` を廃止）
- [ ] ログの書式を `%s` から `{}` へ直す（ログ呼び出しは全部で 59 か所、
      うち 43 か所が `%s`）
- [ ] `__main__.py`: `init_handler()` をやめ、各サブコマンドの先頭で
      `loggerInit(debug)` を呼ぶ
- [ ] `my_logger.py` を削除する
- [ ] `tests/conftest.py`: `_reset_logger` を loguru のシンクのリセットに
      置き換える
- [ ] `caplog` で警告を見ている 5 か所を、シンクを張る fixture へ置き換える
      （`tests/test_midi_writer.py` に 4 つ、`tests/test_midi_parser.py` に 1 つ）
- [ ] `CLAUDE.md` のロギングに関する記述を直す
- [ ] pytest / ruff / mypy / basedpyright を通す

`ytstreetorgan` と `tmr` は既に loguru + `mylog.py` に移っており、
`src/ytmidilib/mylog.py` は `ytstreetorgan` のものと同一。ytmidilib だけが
標準 logging の `my_logger.py` を使っている。

決めたこと:

- 各クラスの `self._log` は廃止し、module 直下の `logger` を直接使う
  （`ytstreetorgan` / `tmr` と同じ書き方）
- `debug=` 引数は**互換のため残す**。ただしログの水準を決めるのは
  `loggerInit()` だけになる（loguru は logger ごとの水準を持てない）。
  `ytstreetorgan/apps.py` の `Parser(debug=...)` はそのまま動く
- ライブラリ側で `logger.disable()` はしない（loguru の既定のまま）。
  `ytstreetorgan` は自分の `loggerInit()` でシンクを張り替えているので、
  ytmidilib のログもそこへ流れる
- テストは loguru のシンクを張る fixture で検証する
  （`caplog` は loguru のログを拾わない）

懸念:

- 要求書 2 通目 #10 の「利用側のログ設定を乗っ取らない」は、loguru を
  設定しないアプリに取り込まれた場合には**成り立たなくなる**
  （loguru の既定シンクは stderr / DEBUG）。上記のとおり、
  それは承知の上で `logger.disable()` はしない
- `my_logger` を無くすのは利用側から見て破壊的変更。回答書
  `docs/20260806b-ytmidilib-responses.md` の「`init_handler()` は
  アプリ専用」という記述が古くなるが、回答書は日付入りの記録なので
  直さず、`ytstreetorgan` へは別途伝える

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-006.** テストを整備する（pytest）](archives/todo/TODO-006.%20テストを整備する（pytest）.md)
- [**TODO-005.** CLI サブコマンド `transpose` の追加](archives/todo/TODO-005.%20CLI%20サブコマンド%20transpose%20の追加.md)
- [**TODO-004.** 要求書 2 通目への回答書を作成する](archives/todo/TODO-004.%20要求書%202%20通目への回答書を作成する.md)
- [**TODO-003.** MIDI ファイルの移調（要求書 2 通目）](archives/todo/TODO-003.%20MIDI%20ファイルの移調（要求書%202%20通目）.md)
- [**TODO-002.** 改善要求への回答書を作成する](archives/todo/TODO-002.%20改善要求への回答書を作成する.md)
- [**TODO-001.** `ytstreetorgan` からの改善要求への対応](archives/todo/TODO-001.%20ytstreetorgan%20からの改善要求への対応.md)

---

## 補足

タグ付けと push は**ユーザーが行う**（Claude は commit まで）。
TODO-001 で `0.1.0` を付与済み。TODO-003〜006 の分は `0.2.0` 想定で未付与。

# TODO

**残っている項目: TODO-014。** これまでに 13 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-015` から。**

---

## TODO-014. `click_utils.py` を導入する

- [ ] `__init__.py` に `__version__` を追加する（`__all__` にも）
- [ ] `__main__.py` の全コマンドを `click_common_opts` に載せ替える
- [ ] `tests/test_cli.py` に `-V` / `--version` のテストを足す
- [ ] `docs/REFERENCE.md` のオプション表を更新する
- [ ] テスト・lint 3 種を通す

`src/ytmidilib/click_utils.py` は置いてあるが、まだどこからも使われて
いない。`ytstreetorgan` / `tmr` と同一のファイルなので、中身には手を
入れない（`mylog.py` と同じ扱い）。

決めたこと:

- `-v` は既存を優先し、全コマンドで `use_v=False` にする。`parse -v` は
  `--visual`、`wav -v` は `--vol` のまま。version は `-V` / `--version` だけ
- `__version__` は `ytstreetorgan` と同じ `importlib.metadata` 方式
- `click_common_opts` は `click.pass_context` を含むので、各コマンドの
  第 1 引数に `ctx` が増える。`cli` group の `@click.pass_context` は
  二重になるので外す
- debug の引数名は `dbg` から `debug` へ統一（デコレータ側が固定のため）

モデル / effort: Opus / high（単独）

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-013.** `write()` を file-like に対応させる（要求書 3 通目）](archives/todo/TODO-013.%20write%28%29%20を%20file-like%20に対応させる（要求書%203%20通目）.md)
- [**TODO-012.** ユーザー全体の `CLAUDE.md` に合わせて記述を整える](archives/todo/TODO-012.%20ユーザー全体の%20CLAUDE.md%20に合わせて記述を整える.md)
- [**TODO-011.** README.md とリファレンスマニュアルの重複を解消する](archives/todo/TODO-011.%20README.md%20とリファレンスマニュアルの重複を解消する.md)
- [**TODO-010.** 要求書・回答書の移動にリンクを追従させる](archives/todo/TODO-010.%20要求書・回答書の移動にリンクを追従させる.md)
- [**TODO-009.** 未使用の依存 `sounddevice` を外す](archives/todo/TODO-009.%20未使用の依存%20sounddevice%20を外す.md)
- [**TODO-008.** リファレンスマニュアルを作る](archives/todo/TODO-008.%20リファレンスマニュアルを作る.md)
- [**TODO-007.** `my_logger.py` を廃止して `mylog.py` へ切り替える](archives/todo/TODO-007.%20my_logger.py%20を廃止して%20mylog.py%20へ切り替える.md)
- [**TODO-006.** テストを整備する（pytest）](archives/todo/TODO-006.%20テストを整備する（pytest）.md)
- [**TODO-005.** CLI サブコマンド `transpose` の追加](archives/todo/TODO-005.%20CLI%20サブコマンド%20transpose%20の追加.md)
- [**TODO-004.** 要求書 2 通目への回答書を作成する](archives/todo/TODO-004.%20要求書%202%20通目への回答書を作成する.md)
- [**TODO-003.** MIDI ファイルの移調（要求書 2 通目）](archives/todo/TODO-003.%20MIDI%20ファイルの移調（要求書%202%20通目）.md)
- [**TODO-002.** 改善要求への回答書を作成する](archives/todo/TODO-002.%20改善要求への回答書を作成する.md)
- [**TODO-001.** `ytstreetorgan` からの改善要求への対応](archives/todo/TODO-001.%20ytstreetorgan%20からの改善要求への対応.md)

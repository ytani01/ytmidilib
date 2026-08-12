# TODO-007. `my_logger.py` を廃止して `mylog.py`（loguru）へ切り替える

## きっかけ

`ytstreetorgan` と `tmr` は既に loguru + `mylog.py` に移っており、
`src/ytmidilib/mylog.py`（`ytstreetorgan` のものと同一のコピー）も置いて
あった。ytmidilib だけが標準 logging の `my_logger.py` を使っていて、
書き方が揃っていなかった。

## 決めたこと

- 各クラスの `self._log` は廃止し、module 直下の `logger` を直接使う
  （`ytstreetorgan` / `tmr` と同じ書き方）
- `debug=` 引数は**互換のため残す**。ただしログの水準を決めるのは
  `mylog.loggerInit()` だけで、この引数は水準に影響しない
  （loguru は logger ごとの水準を持てない）。`ytstreetorgan/apps.py` の
  `Parser(debug=...)` / `Player(rate=..., debug=...)` はそのまま動く
- ライブラリ側で `logger.disable()` はしない（loguru の既定のまま）。
  `ytstreetorgan` は自分の `loggerInit()` でシンクを張り替えているので、
  ytmidilib のログもそこへ流れる
- `mylog.py` は 3 プロジェクトで同一に保つため、**中身は一切変えずに
  コピーのまま**にした（docstring の例に `logInit` / `debg` という
  書き間違いがあるが、直すなら他のプロジェクトも揃えて直す）

## やったこと

- `pyproject.toml` の依存に `loguru>=0.7.3` を足した（`uv add`）。
  mypy の overrides には既に `loguru` が入っていた
- `midi_parser.py` / `midi_player.py` / `wav_utils.py` から `self._log` を、
  `midi_utils.py` / `midi_writer.py` から module 直下の `LOG` を消し、
  `from loguru import logger` に統一（ログ呼び出しは全部で 59 か所）
- ログの書式を `%s` から `{}` へ直した（43 か所）。
  `logger.debug(msg.__dict__)` は loguru の型が `str` を要求するので
  `logger.debug('{}', msg.__dict__)` にした
- `__main__.py`: `init_handler()` をやめ、click の group と各サブコマンドの
  先頭で `loggerInit(debug)` を呼ぶ形にした
- `my_logger.py` を削除した
- `CLAUDE.md` のロギングに関する記述（テストの方針 / アーキテクチャ /
  慣習）を直した

### 破壊的変更

`ytmidilib.my_logger` が無くなった。`get_logger()` / `init_handler()` /
`CONSOLE_HANDLER` / `ROOT_LOGGER_NAME` はもう無い。標準 logging 側から
ytmidilib のログを制御することもできない（loguru のシンクで受ける）。

そのため、要求書 2 通目 #10 で答えた「ライブラリはハンドラを付けない／
利用側のログ設定を乗っ取らない」は、**loguru を設定しないアプリに
取り込まれた場合には成り立たない**（loguru の既定シンクは stderr /
DEBUG）。承知の上で `logger.disable()` はしていない。

回答書 `archives/20260806b-ytmidilib-responses.md` の
「`my_logger.init_handler()` はアプリ専用」という記述は古くなるが、
回答書は日付入りの記録なので直していない。`ytstreetorgan` へは別途伝える。

## テスト

- `tests/conftest.py`
  - autouse の `_reset_logger` を、loguru のシンクを空にする形
    （`logger.remove()`）に置き換えた。CLI のテストが
    `loggerInit()` を通るとシンクが増え、あとのテストの出力に混ざるため
  - `log_messages` fixture を新設。loguru のログは pytest の `caplog` に
    入らないので、シンクを張って `(水準の名前, メッセージ)` に集める
- `caplog` で警告を見ていた 5 か所を `log_messages` に置き換えた
  （`test_midi_writer.py` に 4 つ、`test_midi_parser.py` に 1 つ）
- `pytest` 108 件成功、`ruff` / `mypy` / `basedpyright` すべて
  エラー0・警告0
- CLI も実際に動かして確かめた（`parse` / `parse -v` / `parse -d` /
  `wav -n` / `wav -n -d` / `transpose --clip` / 範囲外のエラー /
  引数なしの help）。`-d` なしで DEBUG が出ないこと、`-d` で出ること、
  移調のクリップ警告が出ることを確認

## タグ

バージョンは hatch-vcs が git タグから決めるので、ここまでのタグの経緯を
残しておく（タグを打つのはユーザー。TODO-012 で `CLAUDE.md` の `git` 節に
明記した）。

- `0.1.0` — TODO-001 の分
- `0.2.0` — TODO-003〜007 の分。元は `eb27a16`（`0.1.1` と同じコミット）を
  指していたが、この項目の分へ付け直し、`develop` と一緒に origin へ
  反映済み（`master` は `eb27a16` のまま）

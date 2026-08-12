# TODO-013. `write()` を file-like に対応させる（要求書 3 通目）

## きっかけ

出典: `archives/20260812a-ytmidilib-requests-3.md`（2026-08-12、対象 0.2.1）

要求元 (`ytstreetorgan`) からの 3 通目。要求は 1 件だけで、[[TODO-003]] で
`transpose_file()` に入れた file-like 対応を `write()` にも入れてほしい、
という話。要求元は「バイト列が欲しい」だけのために一時ディレクトリを
作って書いて読み戻して消しており、型を広げるだけでこれが不要になる。

回答書の作成とタグ付けは、利用者の指示で必須とした（2026-08-12）。

## やったこと

`src/ytmidilib/midi_writer.py`:

- `write()` の第 1 引数を `str | os.PathLike[str] | BinaryIO` に広げた
- 保存を `filename=` / `file=` で分岐（`transpose_file()` の末尾と同じ形）
- docstring の `midi_file` の説明を、パスと file-like の両方を受ける形に

**引数名は `midi_file` のまま据え置いた。** 要求書からの明示の依頼で、
`dst` への改名はキーワード引数で呼ぶ利用者を壊すだけのため。

`docs/REFERENCE.md` 7.2 に、`transpose_file()` の `dst` と同じ扱いである
ことと、`io.BytesIO` を使う例を足した。

`Parser.parse()` の file-like 対応は**入れなかった**（要求書自身が
受け入れ条件から外していた）。理由は回答書に書いたとおり 2 つ:
要求元に用途が無いことと、`parse()` はファイル名をログとエラー
メッセージに出しているので「同じ分岐を足すだけ」では済まないこと。
**やらないと決めたわけではなく、用途ができたら決める。**

回答書: `archives/20260812b-ytmidilib-responses-3.md`
（要求書の「これまでの経緯」の表にも 3 通目の行を足した）

## テスト

`tests/test_midi_writer.py` に 2 件追加（110 passed）。

- `test_write_bytesio` — file-like に書いたものが `mido.MidiFile(file=...)`
  で読み戻せ、パスに書いたものとトラック数・`ticks_per_beat`・
  メッセージ列まで一致する
- `test_write_str_path` — `str` のパスでも書ける

既存の `write()` のテストはすべて `pathlib.Path` 渡しで、無変更のまま通る。

`pytest` / `ruff` / `mypy` / `basedpyright` の 4 つとも、エラー 0・警告 0。

タグ `0.3.0` は利用者の指示で打った。**push は利用者が判断する。**

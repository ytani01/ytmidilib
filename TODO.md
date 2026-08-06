# TODO

**残っている項目: TODO-008。** これまでに 7 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-009` から。**

---

## TODO-008. `docs/REFERENCE.md`（リファレンスマニュアル）を作る

- [ ] `docs/REFERENCE.md` を書く
- [ ] `README.md` から参照を張る

`ytmidilib` は `ytstreetorgan` 専用ではなく、他のアプリからも使われうる。
今は `README.md` が「詳しくは `pydoc` を見よ」と案内するだけで、公開 API
（`__init__.py` の `__all__`）を一覧できる場所が無い。利用側が
`pydoc` を叩かずに読める形にまとめる。

対象は公開 API と CLI に限る。内部実装（`parse1()` / `set_end_time()` /
`_play_main()` など）は仕組みの説明が要る範囲だけ触れ、詳細は
`CLAUDE.md` に任せる。

構成案:

1. はじめに（何をするライブラリか、対象読者、インストール）
2. クイックスタート（パース → 再生の最小コード）
3. データ構造（`ParsedMidi` / `NoteInfo` / `VisualData`）
4. API リファレンス（`__all__` の順に、シグネチャ・引数・戻り値・例外・例）
   - `Parser`、`Player`、`Wav`
   - `write()` / `transpose()` / `transpose_file()`
   - `note2freq()` と定数（`FREQ_BASE` / `NOTE_BASE` / `NOTE_N`
     / `DEF_TICKS_PER_BEAT` / `DRUM_CHANNEL`）
5. ログ（`mylog.loggerInit()`、`debug=` 引数が水準に影響しないこと）
6. CLI リファレンス（`parse` / `play` / `wav` / `transpose`）
7. 注意点・制限（`parse()` → `write()` は往復にならない、
   音声デバイスが要る経路、mixer はモノラルで共有）

決めること:

- 分量。全 API を網羅するか、よく使うものを厚く書くか
- 日本語のみで書く（既存ドキュメントに合わせる）想定でよいか

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-007.** `my_logger.py` を廃止して `mylog.py` へ切り替える](archives/todo/TODO-007.%20my_logger.py%20を廃止して%20mylog.py%20へ切り替える.md)
- [**TODO-006.** テストを整備する（pytest）](archives/todo/TODO-006.%20テストを整備する（pytest）.md)
- [**TODO-005.** CLI サブコマンド `transpose` の追加](archives/todo/TODO-005.%20CLI%20サブコマンド%20transpose%20の追加.md)
- [**TODO-004.** 要求書 2 通目への回答書を作成する](archives/todo/TODO-004.%20要求書%202%20通目への回答書を作成する.md)
- [**TODO-003.** MIDI ファイルの移調（要求書 2 通目）](archives/todo/TODO-003.%20MIDI%20ファイルの移調（要求書%202%20通目）.md)
- [**TODO-002.** 改善要求への回答書を作成する](archives/todo/TODO-002.%20改善要求への回答書を作成する.md)
- [**TODO-001.** `ytstreetorgan` からの改善要求への対応](archives/todo/TODO-001.%20ytstreetorgan%20からの改善要求への対応.md)

---

## 補足

push は**ユーザーが行う**（Claude は commit まで）。タグは、頼まれた
ときだけ Claude が動かす。

TODO-001 で `0.1.0`、TODO-003〜007 の分を `0.2.0` として付与済み。
`0.2.0` は元は `eb27a16`（`0.1.1` と同じコミット）を指していたが、
TODO-007 の分へ付け直し、`develop` と一緒に origin へ反映済み
（`master` は `eb27a16` のまま）。

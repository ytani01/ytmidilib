# TODO

**残っている項目: TODO-013。** これまでに 12 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-014` から。**

---

## TODO-013. `write()` を file-like に対応させる（要求書 3 通目）

- [ ] `write()` の第 1 引数の型を `str | os.PathLike[str] | BinaryIO` に広げる
- [ ] 保存を `filename=` / `file=` で分岐させる（`transpose_file()` 末尾と同じ形）
- [ ] docstring に、パスと file-like のどちらも受けることを書く
- [ ] `docs/REFERENCE.md` の 7.2 に同じことを書く
- [ ] `io.BytesIO` へ書いたものが `mido.MidiFile(file=...)` で読み戻せる
      ことと、パスに書いたものと一致することのテストを足す
- [ ] `pytest` / `ruff` / `mypy` / `basedpyright` を全部通す
- [ ] 回答書 `archives/20260812b-ytmidilib-responses-3.md` を作る
- [ ] 要求書の「これまでの経緯」の表に 3 通目の行を足す
- [ ] コミットまで済んだら、`0.3.0` のタグを打つ

[要求書 3 通目](archives/20260812a-ytmidilib-requests-3.md)（要求元:
`ytstreetorgan`、対象は `0.2.1`）への対応。今回の要求は 1 件だけ。

2 通目で `transpose_file()` に入れた file-like 対応が `write()` に無い
ため、要求元は「バイト列が欲しい」だけのために一時ディレクトリを作って
書いて読み戻して消している。型を広げるだけで、既存の呼び出しは壊れない。

決めること・注意すること:

- **引数名は `midi_file` のまま据え置く。** 要求元から明示の依頼があり、
  `dst` への改名はキーワード引数で呼ぶ利用者を壊す
- **型注釈も広げる**（実装だけ通っても、要求元の `mypy` が落ちる）
- `Parser.parse()` の file-like 対応は**要求に含まれない**。やるか
  どうかはこちらで判断する
- **回答書は必須**（利用者の指示）。これまで（TODO-002 / TODO-004）と
  同じく `archives/` に置き、要求書と相互にリンクする
- **タグ `0.3.0` も打つ**（利用者の指示）。push するかどうかは利用者が
  判断するので、こちらは打つところまで

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

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

# TODO

**残っている項目は無い。** これまでに 7 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-008` から。**

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
TODO-007 のコミットへ付け直した。**origin 側は `eb27a16` を指したまま**
なので、反映するには `git push --force origin 0.2.0` が必要。

# TODO

**残っている項目: TODO-011。** これまでに 10 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-012` から。**

---

## TODO-011. README.md とリファレンスマニュアルの重複を解消する

- [ ] README.md から、`docs/REFERENCE.md` と重複する記述を削除する

`docs/REFERENCE.md` を作った（TODO-008）あと、README.md をそのままに
してあるので、同じことが 2 か所に書かれている。

| README の箇所 | REFERENCE の対応箇所 |
|---|---|
| TL;DR のサンプル | 2.1 パージングして再生する |
| 1. Install | 1. インストール |
| 2. デモ実行 | 9. コマンドライン |
| 3.1 API（pydoc のコマンド列） | 4 / 5 / 7 章 |
| 3.2 parsed data | 3.1 `ParsedMidi` |
| A. Reference（mido へのリンク） | 付録. 関連ドキュメント |

README.md は「何ができるか」と「どこを読めばよいか」だけにし、
API・データ構造・コマンドラインの詳細は REFERENCE.md に任せる。
最短で試せる導線（インストール 1 つとコマンド 1 つ）は、
リンクだけでは足りないので README にも残す。

なお README の `uv run python -m pytoc ytmidilib.note2freq` は
`pydoc` の誤記。削除する範囲に入る。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

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

---

## 補足

push は**ユーザーが行う**（Claude は commit まで）。タグは、頼まれた
ときだけ Claude が動かす。

TODO-001 で `0.1.0`、TODO-003〜007 の分を `0.2.0` として付与済み。
`0.2.0` は元は `eb27a16`（`0.1.1` と同じコミット）を指していたが、
TODO-007 の分へ付け直し、`develop` と一緒に origin へ反映済み
（`master` は `eb27a16` のまま）。

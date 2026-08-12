# TODO

**残っている項目: TODO-012。** これまでに 11 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-013` から。**

---

## TODO-012. ユーザー全体の CLAUDE.md に合わせて記述を整える

- [ ] 造語「契約」を置き換える（`CLAUDE.md` / `docs/REFERENCE.md`）
- [ ] `CLAUDE.md` にタスク管理の節を足す
- [ ] `CLAUDE.md` の `git` 節にタグの扱いを足す
- [ ] `TODO.md` の「補足」節を整理する

ユーザー全体の `CLAUDE.md` が更新されたので、その内容とこのリポジトリの
記述を突き合わせた。差分は 4 点。

1. **造語「契約」。** ユーザー全体の `CLAUDE.md` が名指しで禁止している。
   `CLAUDE.md`（「この dict がモジュール間の唯一の契約」）と
   `docs/REFERENCE.md`（「このモジュール間の唯一の契約」）の 2 か所。
   「モジュール間で受け渡す唯一の形式」に置き換える。`archives/` には
   出てこないので、直すのはこの 2 か所だけ。
2. **タスク管理の説明が無い。** `CLAUDE.md` の本文は `（TODO-007）`
   `（TODO-009）` と番号で参照しているのに、`TODO.md` と
   `archives/todo/` が何なのかがどこにも書かれていない
   （`docs/REFERENCE.md` に一行あるだけ）。手順はユーザー全体の
   `CLAUDE.md` にあるので、**重複させずに**位置づけだけ短く書く。
3. **タグの扱いが `git` 節に無い。** push は書いてあるが、「タグは
   頼まれたときだけ」は `TODO.md` の補足にしかない。バージョンは
   hatch-vcs でタグから決まる（タグを打つのはリリース判断）ので、
   `git` 節に置く。
4. **`TODO.md` の「補足」節に決まりと経緯が混ざっている。**
   骨格に補足節は無い。push / タグの決まりは 3 で `CLAUDE.md` へ移し、
   `0.1.0` / `0.2.0` を付けた経緯は archives 側へ移す。

対応しないもの:

- `TODO.md` の骨格、`archives/todo/` の「きっかけ / やったこと / テスト」は
  すでに合っている
- サブエージェント（`archives/agents/` / `.claude/agents/`）は該当する
  項目がまだ無いので、先にディレクトリは作らない
- 「コミットを 2 回に分ける」はユーザー全体の `CLAUDE.md` にあり、履歴も
  従っている。プロジェクト側に重複させない

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

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

---

## 補足

push は**ユーザーが行う**（Claude は commit まで）。タグは、頼まれた
ときだけ Claude が動かす。

TODO-001 で `0.1.0`、TODO-003〜007 の分を `0.2.0` として付与済み。
`0.2.0` は元は `eb27a16`（`0.1.1` と同じコミット）を指していたが、
TODO-007 の分へ付け直し、`develop` と一緒に origin へ反映済み
（`master` は `eb27a16` のまま）。

# TODO

**残っている項目: TODO-022 .. TODO-024。** これまでに 21 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-025` から。**

以下の 3 項目は、全体をあらためて読み直して洗い出したリファクタリング。
番号の順に優先度の意味は無く、着手する項目は利用者が指定する。

ただし **023 は `midi_writer.py` が重なる**（021 は決着済み）。

---

## TODO-022. `Player` の引数の引き回しを整理する

- [ ] `sec_min` / `sec_max` の持たせ方を決めて、決めたとおりにする
- [ ] `play_th()` の `if not note_info` を `is None` にする
- [ ] `play_th()` の、debug ログのためだけの時刻計算を見直す
- [ ] `WavApp.__init__()` の `print()` を `main()` へ移す

モデル / effort: Sonnet / medium

`sec_min` / `sec_max` は `play()` で 1 度決まる値なのに、`snd_key()` /
`mk_wav()` / `play_sound()` / `play_th()` / `_play_main()` の 5 つが
受け取って下へ渡すだけになっている。インスタンスに持たせれば済む。

（決めること）`snd_key()` は公開メソッドで、テストも引数付きで呼んで
いる。引数を消すか、既定値を付けて両方の呼び方を通すか。

`play_th()` の終了判定 `if not note_info:` は `is None` の意図。
`NoteInfo` に `__bool__` は無いので動きは同じだが、読んで分かる形では
ない（TODO-016 で `set_end_time()` の `if ent:` を直したのと同じ種類）。
同じメソッドの `my_clock_base` / `now` は、debug ログに出す以外に
使っていない。

`WavApp.__init__()` は、`-m` のときに周波数への変換結果を `print()`
している。コンストラクタの副作用なので `main()` の方が収まりが良い。

---

## TODO-023. 定数の置き場所と、`deepcopy` をやめる

- [ ] `DRUM_CHANNEL` を `midi_utils.py` へ移す
- [ ] `set_end_time()` の `copy.deepcopy` をやめる
- [ ] 繰り返している「絞り込むチャンネル」の型に別名を付ける

モデル / effort: Sonnet / low

`DRUM_CHANNEL`（9）は `midi_writer.py` にあるが、MIDI 仕様の定数で、
`__main__.py`（`--drums` のヘルプ）と `tests/conftest.py` からも使って
いる。`DEFAULT_TEMPO` を `midi_utils.py` へ移したのと同じ理由が当て
はまる（TODO-016）。公開 API なので、`__init__.py` の `__all__` と
`docs/REFERENCE.md` の表も追随させる。

`set_end_time()` の `copy.deepcopy(in_data)` は、スカラーしか持たない
dataclass には過剰。元のリストを変更しない性質は保ったまま、新しい
`NoteInfo` を作る形にできる。5 万音で実測:

```
deepcopy    : 0.284 sec
replace()   : 0.077 sec
```

`list[int] | tuple[int, ...] | None` は `midi_parser.py` の
`parse1()` / `parse()` と、`Parser` の同名メソッドの 4 か所にある。
TODO-021 と同じく `type` 文で別名を付けられる。

---

## TODO-024. `click_utils.py` / `mylog.py` に型注釈を付ける

- [ ] 3 プロジェクトを揃えるかどうかを決める
- [ ] 型注釈を付ける

モデル / effort: Sonnet / medium

CLAUDE.md には「型ヒントは全モジュールに付いている」と書いてあるが、
実際には次が未注釈:

- `click_utils.py` の `click_common_opts()` の戻り値、内側の
  `_decorator(func)` の引数と戻り値
- `mylog.py` の `loggerInit()` の `out=sys.stderr`、`exmsg()` の `ex`

**この 2 ファイルは `ytstreetorgan` / `tmr` と同一**なので、直すなら
3 プロジェクトで揃える必要がある（TODO-007 / TODO-014）。

（決めること）3 プロジェクトを同時に直すか、この場では CLAUDE.md の
記述の方を実態に合わせるか。デコレータの型は
`Callable[..., Any]` で済ませるか `ParamSpec` を使うかも決める。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-021.** `midi_writer.py` の型を締める](archives/todo/TODO-021.%20midi_writer.py%20の型を締める.md)
- [**TODO-020.** `play -s` で、頭出し位置の秒数だけ無音で待つ](archives/todo/TODO-020.%20play%20-s%20で、頭出し位置の秒数だけ無音で待つ.md)
- [**TODO-019.** docstring の言語とスタイルを揃える](archives/todo/TODO-019.%20docstring%20の言語とスタイルを揃える.md)
- [**TODO-018.** CLI の定型処理と、重複した小さな処理をまとめる](archives/todo/TODO-018.%20CLI%20の定型処理と、重複した小さな処理をまとめる.md)
- [**TODO-017.** `Wav.mk_wav()` が短すぎる音で失敗する](archives/todo/TODO-017.%20Wav.mk_wav%28%29%20が短すぎる音で失敗する.md)
- [**TODO-016.** `Parser` の責務と、解析結果の型を整える](archives/todo/TODO-016.%20Parser%20の責務と、解析結果の型を整える.md)
- [**TODO-015.** ruff の規則を増やす](archives/todo/TODO-015.%20ruff%20の規則を増やす.md)
- [**TODO-014.** `click_utils.py` を導入する](archives/todo/TODO-014.%20click_utils.py%20を導入する.md)
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

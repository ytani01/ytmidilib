# TODO

**残っている項目: TODO-018 .. TODO-019。** これまでに 17 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-020` から。**

以下の 2 項目は、全体を読み直して洗い出したリファクタリングの残り
（015 / 016 / 017 は決着済み）。**番号の順に着手する**ことを想定して
並べてある（この一連の項目に限り、番号が着手順を表す）。理由は次の
とおり。

- **019（docstring）を最後に。** 構造が動く前に整えると書き直しになる

残りは 2 つとも Sonnet なので、モデルの切り替えは要らない。

| 番号 | 見出し | モデル / effort |
|---|---|---|
| 018 | CLI の定型処理と、重複した小さな処理をまとめる | Sonnet / medium |
| 019 | docstring の言語とスタイルを揃える | Sonnet / low |

---

## TODO-018. CLI の定型処理と、重複した小さな処理をまとめる

- [x] 4 つのサブコマンドで繰り返している形を 1 か所にまとめる
- [x] `loggerInit()` が二重に呼ばれるのを整理する
- [x] click のコマンド関数に引数の型注釈を付ける
- [x] 範囲に丸める処理（3 か所）
- [x] pygame mixer の初期化 / 終了（2 か所）
- [x] パスと file-like の分岐（`midi_writer.py` に 3 か所）
- [x] `play_sound()` の音量計算の数値に名前を付ける

モデル / effort: Sonnet / medium

mixer の初期化は `__main__.py` と `midi_player.py` にまたがっていて、
CLI の整理と同じ範囲を触る。まとめて 1 項目にした。

### CLI

`__main__.py` の `parse` / `play` / `wav` / `transpose` は、どれも

```python
loggerInit(debug)
logger.debug('command={!r}', ctx.command.name)
app = ...App(...)
try:
    app.main()
finally:
    logger.debug('finally')
    app.end()
```

の形を繰り返している。`main()` / `end()` を持つ App を受け取って
呼ぶヘルパーにまとめられる。

`cli` group でも `loggerInit(debug)` を呼んでいるので、サブコマンドを
実行すると 2 回初期化される（`logger.remove()` してから `add()` する
ので実害は無いが、意図が読み取りにくい）。

click のコマンド関数は戻り値にしか型注釈が無い。CLAUDE.md の
「型ヒントは全モジュールに付いており、新規コードでも省略しない」と
食い違っている。

### 重複

`min(max(...))` で範囲に丸める処理が 3 か所にある。

- `midi_player.py` の `Player.within_range()`
- `wav_utils.py` の `Wav.play()`（音量）
- `midi_writer.py` の `_shift_note()`（ノート番号）

`pygame.mixer.init(frequency=..., channels=1)` は `Player.init_mixer()`
と `WavApp.main()` の両方にある。`quit()` も `Player.close()` と
`WavApp.end()` の 2 か所。

`midi_writer.py` の `isinstance(x, (str, os.PathLike))` による分岐は、
`transpose_file()` に 2 つ（読み / 書き）、`write()` に 1 つある。

`play_sound()` の `snd.set_volume(note_info.velocity / 128 / 8)` は、
128 も 8 も説明が無い。

（決めること）共通化したものをどこに置くか。`within_range()` は
`Player` の公開 staticmethod でテストもあるので、移すなら
呼び出し側の互換を考える。
→ **`midi_utils.py` に共通関数を作り、`Player.within_range()` はそれを
呼ぶ薄いラッパーにする。** 既存の公開 staticmethod・テストはそのまま
残す。

---

## TODO-019. docstring の言語とスタイルを揃える

- [ ] 英語のまま残っている docstring を日本語にする
- [ ] `mylog.py` / `click_utils.py` の扱いを決める
- [ ] CLAUDE.md の `snd_key()` の説明を実装に合わせる

モデル / effort: Sonnet / low

**構造を動かす項目（018）が済んでから。** 先にやると、移動や
削除で書き直しになる（016 は決着済み）。

CLAUDE.md では「docstring は numpy スタイル、コメント・ドキュメントは
日本語」としているが、英語のまま残っているものがある
（`play sound`、`keep num within range`、
`parse MIDI format simply for subsequent parsing step` など）。

`mylog.py` は Google スタイル（`Args:`）で書かれていて、他と揃っていない。
`click_utils.py` は型注釈も docstring も薄い。

**この 2 つは `ytstreetorgan` / `tmr` と同一ファイル**なので、直すなら
他のプロジェクトも揃える（TODO-007 / TODO-014 と同じ扱い）。

CLAUDE.md の「長さは 0.02 秒単位に丸めて」は、実装（`snd_key()`）では
0.5 秒を超えるときだけで、0.5 秒以下は 0.01 単位。文書の直しなので
ここでまとめて直す。

（決めること）共有ファイルに手を入れるか、この項目では ytmidilib 固有の
モジュールだけにするか。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

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

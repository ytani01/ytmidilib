# TODO

**残っている項目: TODO-016 .. TODO-019。** これまでに 15 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-020` から。**

以下の 5 項目は、全体を読み直して洗い出したリファクタリング。
**番号の順に着手する**ことを想定して並べてある（この 5 項目に限り、
番号が着手順を表す）。理由は次のとおり。

- **015（ruff）を最初に。** 規則を増やすと既存コードに指摘が出る。
  先に一掃しておけば、あとの項目の差分がリファクタリング本体だけになる
- **016（`Parser`）を次に。** 受け渡しのデータ構造そのものなので、
  ここが決まらないと 018 の CLI 側も揺れる
- **019（docstring）を最後に。** 構造が動く前に整えると書き直しになる
- 017 は独立したバグ修正で、どこに置いても構わない。016 と 018 の間に
  挟んで、**Sonnet で続けて進められる並び**（017 → 018 → 019）にした

モデルの切り替えは 016 の前後の 2 回で済む。

| 番号 | 見出し | モデル / effort |
|---|---|---|
| 015 | ruff の規則を増やす | Sonnet / low |
| 016 | `Parser` の責務と、解析結果の型を整える | Opus / high |
| 017 | `Wav.mk_wav()` が短すぎる音で失敗する | Sonnet / medium |
| 018 | CLI の定型処理と、重複した小さな処理をまとめる | Sonnet / medium |
| 019 | docstring の言語とスタイルを揃える | Sonnet / low |

---

## TODO-016. `Parser` の責務と、解析結果の型を整える

- [ ] `self._channel_set` を持つのをやめる
- [ ] self を使わないメソッドの置き場所を決める
- [ ] 可視化を別モジュールに分けるか決める
- [ ] `set_end_time()` の「最終イベント時刻」の求め方を明示的にする
- [ ] `mk_event_list()` の戻り値に型を付ける
- [ ] `VisualData['data']` に型を付ける
- [ ] `NoteInfo` を dataclass にするか決めて、決めたとおりにする
- [ ] `DEFAULT_TEMPO` を適切なモジュールへ移し、`__all__` に足す
- [ ] `conftest.py` の `DEFAULT_TEMPO` の import を公開 API 経由にする

モデル / effort: Opus / high

責務の整理と型付けは同じコードを触るので、分けると二度手間になる。
`DEFAULT_TEMPO` の移動も `midi_parser.py` に触るため、ここに含めた。

### 責務

`Parser` は `parse()` の中で `self._channel_set` に代入しているが、
同じものを戻り値にも入れていて冗長。外から読む手段も無い。

`parse1()` / `set_end_time()` / `mk_event_list()` / `mk_visual()` は
`self._dbg` 以外に self を使っていない。クラスに属する必要が無い。

可視化（`mk_visual()` / `format_visual()` / `print_visual()`）は
`parse -v` 専用で、再生経路とは独立している。`Parser` から切り離せる。

`set_end_time()` の末尾:

```python
if ent:
    for idx_list in note_start.values():
        ...
```

`ent` はループ変数の残り（最後のエントリ）で、これを「最終イベント時刻」
として使っている。`NoteInfo` に `__bool__` は無いので `if ent:` は
`is not None` と同じだが、読んで分かる形ではない。

### 型

`mk_event_list()` の戻り値と `VisualData['data']` が
`list[dict[str, Any]]` で、イベントの構造がコードから読めない。
`ParsedMidi` / `VisualData` は既に `TypedDict` にしてあるので、
中身も同じように定義する。

`end_time` が `None` のままの `NoteInfo` を `mk_event_list()` に渡すと、
`sorted()` が `None` との比較で `TypeError` になる。`parse()` を通れば
必ず設定されるが、手で組み立てた `NoteInfo` では起きうる。
型を締めるついでに、ここの扱いも決める。

`NoteInfo` は手書きの `__init__`。dataclass にすると `__eq__` が付いて
テストが書きやすくなる（今は同じ内容でも比較できない）。ただし
`abs_time` / `end_time` を `round()` している分は `__post_init__` に移す
必要がある。

### `DEFAULT_TEMPO`

`midi_parser.py` にあるが、`midi_writer.write()` の既定値でもある。
パーサ固有のものではなく MIDI 仕様の既定値なので、`midi_utils.py` の
方が収まりが良い。`__all__` にも無いため、`tests/conftest.py` が
`from ytmidilib.midi_parser import DEFAULT_TEMPO` と内部モジュールを
直接読んでいる。

（決めること）可視化を `midi_visual.py` として分けるか、`Parser` に
置いたままにするか。分けると公開 API とドキュメントの構成も変わる。
`NoteInfo` を dataclass にするかは、公開 API の形が変わるので
`ytstreetorgan` 側への影響も見る。

---

## TODO-017. `Wav.mk_wav()` が短すぎる音で失敗する

- [ ] `out_len == 0` のときにフェードアウトを掛けないようにする
- [ ] サンプル数を整数で求める
- [ ] 短い長さ（0 を含む）のテストを足す

モデル / effort: Sonnet / medium

`wav_utils.py` の `mk_wav()` は、フェードアウトを
`sin_wave[-out_len:] *= ...` で掛けている。`out_len` が 0 になると
`[-0:]` が**配列全体**を指すため、長さ 0 の配列との演算になって
例外が出る。

```
Wav(440, 0.00004, 22050)
-> ValueError: non-broadcastable output operand with shape (1,)
   doesn't match the broadcast shape (0,)
```

`Player` は `SEC_MIN`（0.02 秒）で下限を切るので再生経路では起きないが、
`ytmidilib wav 440 -t 0.00004` では通ってしまう。

同じ箇所の `np.arange(self._rate * self._sec)` は float を渡している。
サンプル数が浮動小数点の丸め任せになるので、整数で求める。

（決めること）長さ 0 を「空の音源」として通すか、エラーにするか。

他の項目から独立している。018 と同じモデル・effort なので、続けて
進められるようにこの位置に置いた。

---

## TODO-018. CLI の定型処理と、重複した小さな処理をまとめる

- [ ] 4 つのサブコマンドで繰り返している形を 1 か所にまとめる
- [ ] `loggerInit()` が二重に呼ばれるのを整理する
- [ ] click のコマンド関数に引数の型注釈を付ける
- [ ] 範囲に丸める処理（3 か所）
- [ ] pygame mixer の初期化 / 終了（2 か所）
- [ ] パスと file-like の分岐（`midi_writer.py` に 3 か所）
- [ ] `play_sound()` の音量計算の数値に名前を付ける

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

---

## TODO-019. docstring の言語とスタイルを揃える

- [ ] 英語のまま残っている docstring を日本語にする
- [ ] `mylog.py` / `click_utils.py` の扱いを決める
- [ ] CLAUDE.md の `snd_key()` の説明を実装に合わせる

モデル / effort: Sonnet / low

**構造を動かす項目（016 / 018）が済んでから。** 先にやると、移動や
削除で書き直しになる。

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

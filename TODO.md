# TODO

作業は大項目ごとに `TODO-NNN` の番号を振る。番号は再利用しない
（完了しても消さず、状態を「完了」に変える）。**大項目は新しい順に並べる。**

| 番号 | 内容 | 状態 |
|---|---|---|
| [TODO-006](#todo-006-テストを整備する-pytest) | テストを整備する（pytest） | 完了 |
| [TODO-005](#todo-005-cli-サブコマンド-transpose-の追加) | CLI サブコマンド `transpose` の追加 | 完了 |
| [TODO-004](#todo-004-要求書-2-通目への回答書を作成する) | 要求書 2 通目への回答書を作成する | 完了 |
| [TODO-003](#todo-003-midi-ファイルの移調要求書-2-通目) | MIDI ファイルの移調（要求書 2 通目） | 完了（タグ付け待ち） |
| [TODO-002](#todo-002-改善要求への回答書を作成する) | 改善要求への回答書を作成する | 完了 |
| [TODO-001](#todo-001-ytstreetorgan-からの改善要求への対応) | `ytstreetorgan` からの改善要求への対応 | 完了（タグ付け待ち） |

---

## TODO-006: テストを整備する（pytest）

`tests/` を新設し、`uv run pytest` で回る自動テストを用意する。

TODO-001 / TODO-003 / TODO-005 の確認は、いずれも**一時ディレクトリの
使い捨てスクリプトによる手動確認**で済ませてきた（各項の「確認方法」）。
セッションが終われば消えるので、**同じ確認を二度とできない**。
回答書（TODO-004）で「確認した」と書く以上、その根拠をリポジトリに
残す。**TODO-004 より先に行う。**

### 方針

- **テスト用のバイナリを置かない。** MIDI ファイルは `mido` で組み立てて
  `tmp_path` に保存する fixture にする（何をテストしているかがコードから
  読め、差分レビューもできる）
- **音声デバイスに触らない。** `pygame.mixer.init()` を通る経路
  （`Player.play()` / `Player.mk_wav()` / `Wav.play()`）はテストしない。
  `Wav` はデータ生成 (`mk_wav()`) と `save()` まで、`Player` は
  純粋な計算 (`within_range()` / `snd_key()`) までを対象にする
- **再生ループ (`_play_main()`) はテストしない。** 実時間の `sleep` に
  依存しており、自動テストにすると遅くて不安定になるだけ
- CLI は `click.testing.CliRunner` を使う（サブプロセスを起動しない）
- `pyproject.toml` の `[tool.pytest.ini_options]` を有効化する。
  `--cov=ytmidilib`（現状はコメントアウトされていて、しかも対象の
  パッケージ名が `tmr` のままなので直す）
- **テストコードも lint / 型チェック 3 種の対象にする。**
  `basedpyright` の `include` に `tests` を足し、`ruff` / `mypy` も
  `tests/` を通す。エラー 0・警告 0 を維持する

### やること（完了）

作ったもの: `tests/` に 7 ファイル、**108 テスト**（0.2 秒で終わる）。

| ファイル | テスト数 |
|---|---|
| `tests/conftest.py` | （fixture のみ） |
| `tests/test_midi_utils.py` | 7 |
| `tests/test_midi_parser.py` | 26 |
| `tests/test_midi_writer.py` | 32 |
| `tests/test_midi_player.py` | 20 |
| `tests/test_wav_utils.py` | 9 |
| `tests/test_cli.py` | 14 |

以下の項目には**取り消し線を引かない**。「何をテストしてあるか」の
一覧として、あとから読む価値があるため。

#### TODO-006-1. 土台

- `tests/conftest.py`
  - `mk_midi_file` — メッセージのリストから MIDI を組み立てて保存する
    ファクトリ
  - `rich_midi_file` — テンポ変化（`set_tempo` 2 つ）・2 トラック・
    `program_change` / `control_change` / `track_name` /
    `time_signature`・ch 9 の音を含む MIDI
    （TODO-003 の手動確認で使ったものと同じ構成）
  - `count_msg_types` — メッセージの種類と数を数える
    （`transpose_file()` の「note 以外は変わらない」の判定に使う）
  - `_reset_logger`（autouse）— **`init_handler()` が落とした
    `propagate` を毎回戻す。** これが無いと、CLI のテストを通った
    あとのテストで `caplog` が何も拾えなくなる（実装中に発覚。
    実行順に依存して落ちるので、原因が分かりにくい類のもの）
- `pyproject.toml` の pytest 設定を有効化
  （`--cov` の対象がコメントの中で `tmr` のままだったので直した）
- `basedpyright` の `include` に `tests` を追加
- `.gitignore` に `.coverage` / `.pytest_cache/` を追加

#### TODO-006-2. `tests/test_midi_utils.py`

- `note2freq(69) == 440.0`
- 1 オクターブ上が 2 倍（`note2freq(81) == 880.0`）、半音が 2^(1/12) 倍
- 範囲の両端（note 0 / 127）でも例外にならない

#### TODO-006-3. `tests/test_midi_parser.py`

- `NoteInfo`
  - `abs_time` / `end_time` が小数第 3 位に丸められる
  - `end_time is None` のとき `length() == 0.0`
  - `__str__()` が `end_time` の有無で形を変える
- `Parser.parse1()`
  - tick → 絶対秒の変換が `set_tempo` の変化に追随する
  - **`set_tempo` が無いファイルでも 120 BPM として正しい秒になる**
  - 複数トラックが 1 本に合成される
  - `channel_set` は**絞り込み前**の全チャンネル
    （`channel=[0]` で絞っても ch 9 が入っている）
  - `note_on` の velocity 0 が note_off として扱われる
- `Parser.set_end_time()`
  - 対応する note_off が `end_time` に入る
  - 同じ (channel, note) が重なったとき、**先に始まった音から順に**
    閉じられる（FIFO）
  - **対応する `note_on` が無い note_off** は警告して読み飛ばす
    （`caplog` で WARNING を 1 行確認する）
  - **閉じられなかった note** は最終イベント時刻で打ち切られる
  - 引数のリストを壊さない（`deepcopy` している）
- `Parser.parse()` — velocity 0 のエントリが落ちる
- `mk_event_list()` — 同時刻でも**同じ note はまとめない**
- `mk_visual()` / `format_visual()`
  - `note_min` / `note_max` が実際に鳴った範囲
  - 開始が `A-Z`、終了が `a-z`、継続中が `|`
  - **同じ note が二重に鳴っているとき**、片方が終わっても `|` のまま
    （`on_count` の意味）
  - `format_visual()` の枠線・ルーラーの桁が揃う

#### TODO-006-4. `tests/test_midi_writer.py`

**ここが本命**（要求書 2 通目の受け入れ条件そのもの）。

- `transpose()`
  - 全 note が n 半音ずれる／負の n で下がる
  - **元のリストを変更しない**（新しいリストを返す）
  - `abs_time` / `end_time` / `velocity` / `channel` は不変
  - ch 9 が `drums=False` で不変、`drums=True` でずれる
  - `clip=False` で範囲外なら `ValueError`、メッセージに note と
    channel が入る
  - `clip=True` で 0 / 127 に丸まり、**丸めたときだけ** WARNING が 1 行
  - `drums=False` のとき、ch 9 は**範囲チェックの対象からも外れる**
    （ch 9 に note 127 があっても `+12` で例外にならない）
- `transpose_file()`
  - **note 以外が変わらない**: メッセージの種類と数・トラック数・
    `ticks_per_beat`・`type` が入出力で一致する
  - `note` だけが指定の半音数ずれている
  - `io.BytesIO` で src / dst を往復できる
  - ch 9 / `clip` / `ValueError` は `transpose()` と同じ規則
    （`_shift_note()` 共通化の担保）
  - **`ValueError` のとき `dst` に何も書かない**
- `write()`
  - `parse()` → `write()` → `parse()` で、**時刻と note と velocity が
    一致する**（往復で音そのものは保たれる）
  - 同時刻に同じ note の消音と再打鍵があるとき、**消音が先**に並ぶ
  - `end_time is None` の音が長さ 0 で書かれる
  - velocity 0 のエントリは書かれない
  - `ticks_per_beat` / `tempo` の引数が出力に反映される

#### TODO-006-5. `tests/test_midi_player.py`

- `within_range()` の下限・上限・範囲内
- `snd_key()`
  - 長さが `sec_min` / `sec_max` に丸め込まれる
  - 0.5 秒以下は 0.01 単位、0.5 秒超は 0.02 単位に丸まる
  - **近い長さの音が同じキーになる**（キャッシュが効く根拠）
- `is_playing()` が初期状態で `False`

#### TODO-006-6. `tests/test_wav_utils.py`

- `mk_wav()`
  - 長さ（サンプル数）と `dtype` が `int16`
  - 振幅が `AMPLITUDE` を超えない
  - **先頭と末尾の振幅が中央より小さい**（フェードが効いている＝
    クリックノイズ対策の担保）。両端はちょうど 0 になる。末尾は
    区間ごとの最大値が単調に小さくなることも見る
  - 周波数が合っていること。**ゼロ交差ではなく FFT のピーク**で見る
    （フェードで末尾が 0 に潰れるぶん、ゼロ交差は数えにくい）
- `save()` した wav を `wave` で読み直し、チャンネル数 1・
  サンプル幅 2・レート・フレーム数が一致する

#### TODO-006-7. `tests/test_cli.py`

`CliRunner` で、音を鳴らさない経路だけ。

- `ytmidilib` 引数なし → ヘルプ、終了コード 0
- `-h` に 4 つのサブコマンドが並ぶ
- `parse FILE` — `channel_set=` が出る
- `parse -v FILE` — 可視化が出る
- `parse -c 0 FILE` — 絞り込みが効く
- `transpose SRC DST 2` — 移調できて、`+2 semitone(s)` が出る
- **`transpose SRC DST -2`**（負の値がオプションと誤解されない）
- 範囲外 → `Error: ... .. use --clip`、終了コード 1、
  **トレースバックが出ない**
- 存在しないファイル → click のエラー（終了コード 2）
- `--clip` / `-D` が効く、`transpose -h` の体裁
- **`wav -n`（再生しない）も対象にした**（要求書には無い追加）。
  `-n` なら `pygame.mixer.init()` を通らないので、デバイス不要で
  保存経路と `-m`（MIDIノート番号）の表示を確認できる

#### TODO-006-8. ドキュメント

- `CLAUDE.md` の「注意点」から「`tests/` は無く〜」を消し、
  「コマンド」節の `uv run pytest` の但し書きを直す
- 「lint / 型チェック（必須）」を「テスト / lint / 型チェック（必須）」
  にして、**テストの実行と対象（`src/ tests/`）**を加える
- 「テストの方針」の節を足す（音声デバイスを使わない理由、
  `init_handler()` と `caplog` の関係）

### 確認方法（確認済み）

- ~~`uv run pytest` が全部通る~~ **108 passed / 0.2 秒**
- ~~lint / 型チェック 3 種がエラー 0・警告 0~~
  （`ruff` / `mypy` は `src/ tests/` の両方、`basedpyright` は
  `include` 経由で `tests` も対象）
- ~~**音声デバイスの無い環境でも通る**~~
  `SDL_AUDIODRIVER=no-such-driver` でも 108 passed。
  `Player` を生成しても `pygame.mixer.get_init()` が `None` のまま
  であることも、テストとして残した
- ~~わざとコードを壊すと落ちる~~ 5 通り試して、すべて検出できた

| 壊した箇所 | 落ちたテスト |
|---|---|
| `_shift_note()` の ch 9 判定を消す | 7 件 |
| `Wav.mk_wav()` のフェードを消す | 1 件 |
| `write()` の消音優先の並びを反転する | 1 件 |
| `set_end_time()` の FIFO を LIFO にする | 1 件 |
| `parse1()` の `set_tempo` 追随をやめる | 3 件 |

**`write()` の並びは、最初のテストでは検出できなかった。** ソートキーの
第 2 要素（消音を先に）を消しても、安定ソートのおかげで入力が時刻順なら
結果が変わらないため。入力を逆順にした場合も含めて確かめる形に直した。

### 完了条件

- ~~上の確認方法をすべて満たす~~ 完了
- ~~**TODO-003 の「確認方法」に手で並べた項目が、すべて自動テストとして
  残っている**~~ 完了（`tests/test_midi_writer.py`）
- ~~新しい要求が来たときに、`uv run pytest` だけで退行を検出できる~~ 完了

### 残った穴（意図的）

- `Player` の再生経路（`play()` / `mk_wav()` / `_play_main()`）は
  カバレッジ 33%。**音声デバイスと実時間に依存するので、意図的に
  テストしていない**（方針を参照）。全体のカバレッジは 80%
- `Wav.play()` も同じ理由で未テスト
- `mido` の再直列化がバイト単位で一致するかは見ていない
  （そもそも保証しない、と回答書に書く）

---

## TODO-005: CLI サブコマンド `transpose` の追加

要求書には無い、こちら側の追加。**TODO-003 の完了後に行う**
（`transpose_file()` の薄いラッパーなので、先に本体が要る）。

```
ytmidilib transpose SRC DST N [--clip] [--drums] [-d]
```

### やること（完了）

- ~~`__main__.py` に `TransposeApp` を追加し、他のサブコマンドに合わせて
  `main()` → `finally: end()` の形で呼ぶ~~
- ~~引数・オプションは `transpose_file()` に 1 対 1 で対応させる~~
  `--clip` / `-c`、`--drums` / `-D`（既定 off ＝ ライブラリ側の既定と同じ）
- ~~`N` が負の値（`-2` など）でもオプションと誤解されないようにする~~
  このコマンドだけ `ignore_unknown_options=True`
  （`TRANSPOSE_CONTEXT_SETTINGS`）
- 範囲外の `ValueError` は `click.ClickException` に包み、
  `.. use --clip` を添えて 1 行で出す（トレースバックを出さない）

### 確認方法（確認済み）

- ~~`ytmidilib transpose a.mid b.mid 2` で移調できる~~
- ~~`ytmidilib transpose a.mid b.mid -2` が通る（負の値）~~
- ~~`--clip` 無しで範囲外なら、エラーが分かる形で表示される~~
  `Error: note out of range: 60 + 100 = 160 (channel:0) .. use --clip`
  （終了コード 1）
- ~~`-h` のヘルプが他のサブコマンドと同じ体裁~~
- ~~lint / 型チェック 3 種がエラー 0・警告 0~~

### 完了条件

- ~~CLI から移調できる~~ 完了
- ~~`ytmidilib -h` に `transpose` が出る~~ 完了

---

## TODO-004: 要求書 2 通目への回答書を作成する

出典: `docs/20260806c-ytmidilib-requests-2.md`（2026-08-06）

TODO-003 の対応内容を、要求元 (`ytstreetorgan`) への回答書としてまとめる。
TODO-002（`docs/20260806b-ytmidilib-responses.md`）と同じ体裁で、
要求書の項番 #1〜#4 ごとに答える。

**TODO-006（テストの整備）の後に書く。** 回答書に書く「確認した」の
根拠を、使い捨てスクリプトではなくリポジトリに残したうえで出す
（ユーザー判断、2026-08-06）。

### やること（完了）

作成物: `docs/20260806d-ytmidilib-responses-2.md`

- ~~`docs/` に回答書を新規作成する（日付＋用途が分かるファイル名）~~
- ~~要求と違う判断をした箇所は理由を明記する~~
  - ~~「1 バイトも変わらない」は保証しない（`mido` の再直列化のため）。
    メッセージ構成の一致で確認したことを書く~~
    **バイト列を比較する検証を組んでいるなら知らせてほしい、と添えた**
  - ~~実装は要求書のコード片ではなく、読み込んだ `MidiFile` を書き換えて
    保存する方式（引き継ぎ漏れが起きないため）~~
    要求書のコード片が `charset` を写していない例を挙げた
  - ~~ch 9 は範囲チェック・クリップの対象からも外した（要求書に無い判断）~~
  - ~~`transpose()` の既定 `drums=False` により 0.1.0 から挙動が変わる~~
    既定を揃えた理由（既定値が違うこと自体が「意味論が 2 つ」に当たる）
- ~~要求書に無い追加（CLI サブコマンド `transpose`。TODO-005）を書く~~
- ~~新しいタグ（`0.2.0` 想定）を書く~~
  要求書が触れていた `uv` の git キャッシュの件にも 1 行返した

要求書に無かったが回答書に書き足した点:

- **テストの整備（TODO-006）**。受け入れ条件がすべて自動テストとして
  残っていること、要求元の再現例と同じ構成の MIDI が fixture にあること
- `ValueError` のとき `dst` に何も書かないこと（要求書に無い保証）
- `transpose()` と `transpose_file()` で `ValueError` のメッセージが
  微妙に違う理由（後者は `NoteInfo` を経由しないので絶対秒が無い）

### 完了条件

- ~~要求書の #1〜#4 に漏れなく回答している~~ 完了
- ~~回答書だけ読めば、要求元が移行作業を始められる~~ 完了

### 残り

- **タグ付け (`0.2.0`) と push はユーザーが行う**（TODO-003 と共通）

---

## TODO-003: MIDI ファイルの移調（要求書 2 通目）

出典: `docs/20260806c-ytmidilib-requests-2.md`（2026-08-06、対象 0.1.0）

要求は 4 件。**#1（`transpose_file()` の新設）が本体**で、#2（`clip`）と
#3（`drums`）はその引数の設計、#4 は `write()` の docstring。

### 守るべき互換性

要求元が使っているのは TODO-001 と同じ表の API（`Parser` / `NoteInfo` /
`Player`）のみ。**`transpose()` / `write()` は要求元未使用**なので、
既定値の変更は要求元を壊さない。それでも `clip` は既定 `False`
（= 現行どおり `ValueError`）にして、既存の挙動は維持する。

### ユーザー判断（2026-08-06）

- `drums` の既定は **`transpose()` / `transpose_file()` とも `False`**
  （ch 9 をずらさない）。`transpose()` は 0.1.0 から挙動が変わる
- 回答書は **TODO-004** に分ける
- **CLI サブコマンド `transpose` を作る**（要求書には無い追加）

### 設計方針

- **元の `MidiFile` をその場で書き換えて保存する。**
  要求書の案（新しい `MidiFile` を組み立て直す）ではなく、
  `mido.MidiFile()` で読んだオブジェクトの `note_on` / `note_off` の
  `note` だけを書き換えて `save()` する。`type` / `ticks_per_beat` /
  `charset` / メタメッセージ / トラック構成が**自動的にそのまま**残り、
  組み立て直しの取りこぼしが原理的に起きない
- **file-like 対応は `str | os.PathLike[str]` かどうかで分岐する。**
  パスなら `mido.MidiFile(filename=...)` / `save(filename=...)`、
  それ以外は `file=` に渡す（`io.BytesIO` が通る）
- **`mido` の型は公開 API に出さない**（引数も戻り値も `mido` 非依存）
- 範囲外・ch 9 の判定は `transpose()` と共通のヘルパーに置き、
  2 つの関数で意味論が食い違わないようにする

**注意**: 「1 バイトも変わらない」は保証しない（`mido` の再直列化で
running status や delta の符号化が変わりうる）。要求書の受け入れ条件に
挙がっている**メッセージの種類と数・トラック数・`ticks_per_beat`・`type`
の一致**を確認基準とする。

### やること（完了）

#### ~~TODO-003-1. `transpose_file()` の新設（#1・機能追加・最優先）~~ 完了

`midi_writer.py` に追加する。

```python
def transpose_file(
    src: str | os.PathLike[str] | BinaryIO,
    dst: str | os.PathLike[str] | BinaryIO,
    n: int,
    clip: bool = False,
    drums: bool = False,
) -> None:
```

- ~~`note_on` / `note_off` の `note` だけをずらす。他は一切触らない~~
- ~~`src` / `dst` は パス と file-like（`io.BytesIO` 等）の両方を受ける~~
- ~~`__init__.py` の `__all__` に追加する~~
  （`transpose_file` に加えて `DRUM_CHANNEL` も公開した）

#### ~~TODO-003-2. `clip` 引数（#2・改善・高）~~ 完了

`transpose()` と `transpose_file()` の**両方**に同じ規則で足した。

- ~~既定 `clip=False` = 範囲外があれば `ValueError`（現行どおり）~~
- ~~`clip=True` = 0〜127 に丸める。丸めたときは **WARNING を 1 行**~~
- ~~1 個も丸めなければ WARNING は出さない~~

#### ~~TODO-003-3. `drums` 引数（#3・改善・中）~~ 完了

- ~~`drums=False`（既定）で **channel 9 をずらさない**~~
- ~~`drums=True` で全チャンネルをずらす~~
- ~~**`transpose()` / `transpose_file()` とも既定 `False`**~~
- ~~範囲チェック・クリップの対象からも ch 9 を外す~~
- ~~docstring に ch 9 の扱いを明記する~~

判定は `_shift_note()`（モジュール内のヘルパー）に集約し、2 つの関数で
意味論が食い違わないようにした。ch 9 の番号は定数 `DRUM_CHANNEL`。

#### ~~TODO-003-4. `write()` の docstring（#4・改善・低）~~ 完了

`NoteInfo` が持たないもの（`program_change` / `control_change` /
`pitch_bend` / メタメッセージ / トラック構成 / テンポ変化）を列挙し、
`transpose_file()` へ誘導する行を足した。

### 確認方法（tests/ が無いので手動）— 確認済み

一時ディレクトリの検証スクリプトで、以下をすべて確認した。

- ~~テンポ変化（2 つの `set_tempo`）・2 トラック・`program_change` /
  `control_change` / `track_name` / `time_signature` を含む MIDI で、
  メッセージの種類と数・トラック数・`ticks_per_beat`・`type` が一致し、
  `note` だけが指定の半音数ずれていること~~
- ~~`io.BytesIO` で src / dst を往復できること~~
- ~~`clip=False` / 引数省略で、範囲外が `ValueError`~~
- ~~`clip=True` で 0〜127 に丸まり、WARNING が 1 行だけ出ること~~
  （丸めが起きなければ出ないことも確認）
- ~~ch 9 の `note` が `drums=False` で不変、`drums=True` でずれること~~
- ~~`transpose()`（`NoteInfo` 版）が元のリストを変更しないこと~~
- ~~lint / 型チェック 3 種がエラー 0・警告 0~~

### 完了条件

- ~~要求書 #1〜#4 の受け入れ条件をすべて満たす~~ 完了
  （ただし「1 バイトも変わらない」は保証せず、メッセージ構成の一致で確認）
- ~~利用側が `import mido` せずに移調を完結できる~~ 完了
- **残り: タグ付け・push。** ユーザーが行う（`0.2.0` 想定）

CLI は TODO-005（完了）、回答書は TODO-004 で行う。

---

## TODO-002: 改善要求への回答書を作成する

出典: `docs/20260806a-ytmidilib-requests.md`（2026-08-06）

TODO-001 で対応した内容を、**要求元 (`ytstreetorgan`) へ返す回答書**として
まとめる。要求元は要求書の項番 (#1〜#13) で管理しているので、
**項番ごとに「どう対応したか」を答える**。

### やること（完了）

作成物: `docs/20260806b-ytmidilib-responses.md`

- ~~`docs/` に回答書を新規作成する（日付＋用途が分かるファイル名）~~
- ~~要求書の一覧表と同じ #1〜#13 の並びで、各項目について書く~~
- ~~要求と違う判断をした箇所（#4 / #7 / #8）は理由を明記する~~
- ~~利用側の移行に必要な情報（挙動が変わるもの・新しいタグ）を書く~~
- ~~追加された API の一覧~~

要求書に無かったが回答書に書き足した点:

- pygame のバナー（#5 の「影響」）は**まだ出る**。mixer の初期化時期とは
  別の話なので、`PYGAME_HIDE_SUPPORT_PROMPT` での回避方法を案内した
- `NoteInfo.__init__` から `debug` 引数が消えていること（移行の表に追加）
- `my_logger.init_handler()` は**ライブラリ利用側は呼ばない**こと

### 完了条件

- ~~要求書の #1〜#13 に漏れなく回答している~~ 完了
- ~~回答書だけ読めば、要求元が移行作業を始められる~~ 完了

### 残り

- **push はユーザーが行う**（タグ `0.1.0` は付与済み）

---

## TODO-001: `ytstreetorgan` からの改善要求への対応

出典: `docs/20260806a-ytmidilib-requests.md`（2026-08-06）

要求は 0.0.3 時点のコードに対するもので、その後の
`0e1a2ea refactor: 型ヒントを追加し、lint の指摘を解消する` で
**要求 #2 / #3 / #7 / #13 は既に解消済み**。

以下、`TODO-001-N` が作業単位、`#N` は要求書の項番。

### 守るべき互換性（要求書「互換性の方針」）

要求元が実際に使っているのは次だけ。**ここが壊れなければ、残りは自由に
変えてよい。** 各作業の前後でこの表を確認する。

| API |
|---|
| `Parser()` / `Parser.parse(midi_file, channel)` |
| `Parser.mk_visual()` / `Parser.print_visual()` |
| `NoteInfo`（`abs_time` / `channel` / `note` / `velocity` / `end_time` / `length()` / `__str__`） |
| `Player()` / `Player.play(parsed, pos, sec_min, sec_max)` |
| `Player.DEF_RATE` / `Player.SEC_MIN` / `Player.SEC_MAX` |

特に注意する箇所:

- TODO-001-5: `block` は**既定値付きの追加引数**にする
  （`play(parsed, pos, sec_min, sec_max)` の呼び出しがそのまま通ること）
- TODO-001-9: `print_visual()` を**消さない**。`format_visual()` を足して
  `print_visual()` はその薄いラッパーにする
- TODO-001-4: `Player()` 生成自体は引き続き成功すること
  （音声デバイス不在で `__init__` が失敗するようにしない）
- #4（TODO-001-3）と #7 は出力・戻り値の形が変わるが、要求元はタグ
  `0.0.3` で固定しているので入れてよい

### 対応済み（要求 #2, #3, #7, #13）

現状のコードを確認した結果、追加作業は不要。

- #2 `NoteInfo.end_time` — `None if end_time is None else round(end_time, 3)`
  になっており、`int` も通る（`midi_parser.py:41`）
- #3 型注釈 — 公開 API に注釈あり。既定値 `None` も撤去済み
- #7 戻り値の型 — `TypedDict` を定義済み。
  要求元の文書に合わせて **`ParsedMidi` に改名した**
  （2026-08-06 ユーザー判断）
- #13 `length()` の docstring — `[sec]` に修正済み。
  `end_time is None` で `0.0` を返す旨も追記した

### やること

優先度順。TODO-001-1 は先に単独でコミットする。

#### ~~TODO-001-1. tempo 既定値 500000 を適用する（#1・不具合・最優先）~~ 完了

- `Parser.parse1()` の `cur_tempo = None` → `cur_tempo = DEFAULT_TEMPO`
  （= 500000。`mido.bpm2tempo(120)`。MIDI 仕様の既定値）
- `if cur_tempo:` の分岐を撤去
- 確認済み: `set_tempo` 無し・480tpb・四分音符の MIDI で `length()` == 0.5、
  `set_tempo` 有りの既存ファイル（pygame の `MIDI_sample.mid`）で
  `parse -v` の出力が変更前と一致

#### ~~TODO-001-2. `set_end_time()` の例外処理（#9・不具合）~~ 完了

- `except KeyError` → `except (KeyError, IndexError)`
- 警告メッセージに channel / note / 時刻を含める
- 確認済み: 対応する note_on が無い note_off を含む MIDI で、警告を出して
  読み飛ばし、残りの note は正しく解析される

#### ~~TODO-001-3. `Player` の標準出力をやめる（#4・改善）~~ 完了

**方針: `print()` は DEBUG ログに置き換える**（要求の選択肢 1。
コールバック `on_note` は採らない）。

- `play_th()` の `print(f'{now:08.3f} / {note_info}')`（`midi_player.py:134`）
  → `self._log.debug('%08.3f / %s', now, note_info)`
- `play()` 末尾の `print('end music')` → `self._log.debug('end music')`
- 既定（`debug=False`）では標準出力・標準エラーに何も出ない
  - `mk_wav()` 後の `_log.info('len(snd)=...')` も DEBUG へ落とした
- CLI で従来の表示が欲しい場合は `-d` を付ける
- 確認済み: `play` 実行時に `Player` からの出力が無いこと

#### ~~TODO-001-4. `pygame.mixer.init()` の遅延化（#5・改善）~~ 完了

- `Player.__init__()` から `pygame.mixer.init()` を外し、`init_mixer()` を
  新設して `mk_wav()` 冒頭で呼ぶ（初期化済みなら何もしない）
- `close()` を追加し、`__enter__` / `__exit__` も付けた
- 音声デバイス不在時は `play()`（`mk_wav()`）で `pygame.error` になる
- `WavApp` も `main()` の再生時のみ初期化するようにし、`end()` で
  `pygame.mixer.quit()`。保存のみ（`-n`）なら音声デバイス不要になった
- `MidiApp.end()` で `Player.close()` を呼ぶ
- 確認済み: `Player()` 生成だけでは mixer が初期化されないこと、
  `with Player()` で初期化 → 終了時に解放されること、
  `parse` / `play` / `wav -n` が従来どおり動くこと

#### ~~TODO-001-5. 再生の停止・非同期化（#6・機能追加）~~ 完了

- `stop()` — `threading.Event` を見て、次の音符の前でループを抜ける。
  ワーカースレッドにも終了を伝え、`pygame.mixer.stop()` で鳴っている音も
  止める。待ちは `sleep()` ではなく `Event.wait()` にして反応を良くした
- `play(..., block: bool = True)` — `False` で別スレッド再生。
  音源生成 (`mk_wav()`) は `block` によらず呼び出し側で先に済ませるので、
  音声デバイス不在のエラーは `play()` から見える
- `is_playing() -> bool`
- 再生中の `play()` は `RuntimeError`（`stop()` を先に呼ぶ）
- `stop()` 後に再度 `play()` できること（Event を毎回クリアする）
- 確認済み: 6秒の MIDI で、`block=False` が即座に戻る／1秒で `stop()` でき
  `is_playing()` が False になる／再度 `play()` できる／
  `play(parsed, pos, sec_min, sec_max)` の従来形が 6 秒ブロックする

#### ~~TODO-001-6. MIDI 書き出し（#8・機能追加）~~ 完了

- 新規 `midi_writer.py`
  - `write(midi_file, note_info, ticks_per_beat=480, tempo=500000) -> None`
  - `NoteInfo` を note_on / note_off に展開し、絶対秒 → tick へ戻す
    （`mido.second2tick`）。同時刻は消音 → 発音の順に並べ、delta=0 で続ける
    （同じ note の再打鍵と衝突させないため）
  - `transpose(note_info, n) -> list[NoteInfo]`。
    **範囲外は `ValueError`**（2026-08-06 ユーザー判断）。1音でも
    範囲外なら移調全体を失敗させる。元のリストは変更しない
- 確認済み: 和音・同一 note の連打を含むデータで
  `parse()` → `write()` → `parse()` が一致（既定 480/500000 に加え、
  96/300000・960/700000 でも一致）。`transpose(+12)` が元を壊さないこと、
  範囲外で `ValueError` になること
- `__init__.py` の `__all__` に `write` / `transpose` /
  `DEF_TICKS_PER_BEAT` を追加

#### ~~TODO-001-7. ロギングをライブラリらしくする（#10・改善）~~ 完了

- `get_logger()` から `addHandler()` / `propagate = False` を外し、
  レベル設定のみにした
- ロガー名を `inspect.stack()` ベースから、パッケージ名 (`ytmidilib.*`)
  ベースへ（`get_logger()` の重さも解消）。`__name__` を渡された場合は
  そのまま使う
- ハンドラの設定は `my_logger.init_handler()` に切り出し、
  `__main__.py` の click group から呼ぶ
- 確認済み: CLI で従来どおりログが出る／`-d` で DEBUG が出る／
  ライブラリとして import しただけではハンドラが付かない／
  アプリ側の `logging.basicConfig()` の書式に従う

#### ~~TODO-001-8. パスを `str | os.PathLike[str]` に（#11・改善）~~ 完了

- `Parser.parse()` のシグネチャと docstring。`mido` 側はそのまま通る
- ついでに `Wav.save()` も同様にした（`wave.open()` の型定義が `str`
  しか受けないので `os.fspath()` を挟む）。`midi_writer.write()` は
  最初から `str | os.PathLike[str]`
- 確認済み: `pathlib.Path` で `parse` / `write` / `save` が通る

#### ~~TODO-001-9. `format_visual()` の追加（#12・改善）~~ 完了

- `format_visual(v_data, channel_set) -> str` を新設し、
  `print_visual()` はそれを `print()` するだけにした
- `_print_note_ruler()` を `_format_note_ruler()`（`list[str]` を返す）へ
- 確認済み: `parse -v` の出力が変更前と完全一致（diff で確認）

### 完了後

- ~~`uv run ruff check src/` / `uv run mypy src/` / `uv run basedpyright` を
  すべて通す~~ 完了（エラー0・警告0）
- ~~互換性の表の API がすべて通ることを確認~~ 完了
- ~~タグ付け~~ 完了。**`0.1.0`**（#4 の出力変更・#5 の初期化タイミング変更・
  `ParsedMidi` への改名を含むため）
- **残り: push。** ユーザーが行う。Claude は commit まで

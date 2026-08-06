# TODO-006. テストを整備する（pytest）

## きっかけ

`tests/` を新設し、`uv run pytest` で回る自動テストを用意する。

[[TODO-001]] / [[TODO-003]] / [[TODO-005]] の確認は、いずれも**一時ディレクトリの
使い捨てスクリプトによる手動確認**で済ませてきた（各項の「確認方法」）。
セッションが終われば消えるので、**同じ確認を二度とできない**。
回答書（[[TODO-004]]）で「確認した」と書く以上、その根拠をリポジトリに
残す。**[[TODO-004]] より先に行う。**

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
  `--cov=ytmidilib`（当時はコメントアウトされていて、しかも対象の
  パッケージ名が `tmr` のままだったので直す）
- **テストコードも lint / 型チェック 3 種の対象にする。**
  `basedpyright` の `include` に `tests` を足し、`ruff` / `mypy` も
  `tests/` を通す。エラー 0・警告 0 を維持する

## やったこと

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

以下は「何をテストしてあるか」の一覧として、あとから読む価値があるので
そのまま残す。

### TODO-006-1. 土台

- `tests/conftest.py`
  - `mk_midi_file` — メッセージのリストから MIDI を組み立てて保存する
    ファクトリ
  - `rich_midi_file` — テンポ変化（`set_tempo` 2 つ）・2 トラック・
    `program_change` / `control_change` / `track_name` /
    `time_signature`・ch 9 の音を含む MIDI
    （[[TODO-003]] の手動確認で使ったものと同じ構成）
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

### TODO-006-2. `tests/test_midi_utils.py`

- `note2freq(69) == 440.0`
- 1 オクターブ上が 2 倍（`note2freq(81) == 880.0`）、半音が 2^(1/12) 倍
- 範囲の両端（note 0 / 127）でも例外にならない

### TODO-006-3. `tests/test_midi_parser.py`

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

### TODO-006-4. `tests/test_midi_writer.py`

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

### TODO-006-5. `tests/test_midi_player.py`

- `within_range()` の下限・上限・範囲内
- `snd_key()`
  - 長さが `sec_min` / `sec_max` に丸め込まれる
  - 0.5 秒以下は 0.01 単位、0.5 秒超は 0.02 単位に丸まる
  - **近い長さの音が同じキーになる**（キャッシュが効く根拠）
- `is_playing()` が初期状態で `False`

### TODO-006-6. `tests/test_wav_utils.py`

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

### TODO-006-7. `tests/test_cli.py`

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

### TODO-006-8. ドキュメント

- `CLAUDE.md` の「注意点」から「`tests/` は無く〜」を消し、
  「コマンド」節の `uv run pytest` の但し書きを直す
- 「lint / 型チェック（必須）」を「テスト / lint / 型チェック（必須）」
  にして、**テストの実行と対象（`src/ tests/`）**を加える
- 「テストの方針」の節を足す（音声デバイスを使わない理由、
  `init_handler()` と `caplog` の関係）

## テスト

- `uv run pytest` が全部通る — **108 passed / 0.2 秒**
- lint / 型チェック 3 種がエラー 0・警告 0
  （`ruff` / `mypy` は `src/ tests/` の両方、`basedpyright` は
  `include` 経由で `tests` も対象）
- **音声デバイスの無い環境でも通る** —
  `SDL_AUDIODRIVER=no-such-driver` でも 108 passed。
  `Player` を生成しても `pygame.mixer.get_init()` が `None` のまま
  であることも、テストとして残した
- わざとコードを壊すと落ちる — 5 通り試して、すべて検出できた

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

完了条件:

- 上の確認をすべて満たす — 完了
- **[[TODO-003]] の「確認方法」に手で並べた項目が、すべて自動テストとして
  残っている** — 完了（`tests/test_midi_writer.py`）
- 新しい要求が来たときに、`uv run pytest` だけで退行を検出できる — 完了

### 残った穴（意図的）

- `Player` の再生経路（`play()` / `mk_wav()` / `_play_main()`）は
  カバレッジ 33%。**音声デバイスと実時間に依存するので、意図的に
  テストしていない**（方針を参照）。全体のカバレッジは 80%
- `Wav.play()` も同じ理由で未テスト
- `mido` の再直列化がバイト単位で一致するかは見ていない
  （そもそも保証しない、と回答書に書く）

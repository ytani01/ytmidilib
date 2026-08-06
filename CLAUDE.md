# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

`ytmidilib` は、MIDIライブラリ `mido` のラッパー。MIDIファイルを
**イベント単位ではなく note 単位** にパージングし、各 note の開始/終了時刻を
曲頭からの絶対秒で持つ形に変換する。さらに、その結果を鳴らす簡易プレーヤーと、
sin波から wav 音源を生成するユーティリティを持つ。音源は外部の音源ファイルや
シンセを使わず、**再生時にすべて sin波で合成する**。

## コマンド

パッケージ管理は `uv`（Python 3.13以上）。

```bash
uv sync                      # 依存関係の同期（dev含む）
uv run ytmidilib parse FILE  # パーサ実行（-v で可視化, -c CH でチャンネル選択）
uv run ytmidilib play FILE   # プレーヤー実行
uv run ytmidilib wav FREQ    # 単音生成/再生（-m で FREQ を MIDIノート番号として扱う）
uv run ytmidilib transpose SRC DST N  # 移調（--clip で範囲外を丸める）
uv tool install .            # ローカルインストール
```

### テスト / lint / 型チェック（必須）

**コードを変更したら、以下の4つを必ず全部通すこと。** どれか1つでも
省略しない（lint 3つはそれぞれ別の問題を検出する。例: `__init__` 内の
`__class__` 参照は mypy だけが、到達不能コードは basedpyright だけが
検出した）。

```bash
uv run pytest                    # テスト（設定は pyproject。tests/ が対象）
uv run ruff check src/ tests/    # スタイル
uv run mypy src/ tests/          # 型
uv run basedpyright              # 型 + 到達可能性など（対象は pyproject の include）
```

現状すべて **エラー0・警告0**、テストは全て成功の状態を維持している。
新しいコードで警告が出たら、抑制コメントで消すのではなく直す。

CI 設定は無いので、上記はローカルで手動実行する。

### テストの方針

`tests/` は **音声デバイスを一切使わない**（無い環境でも通る）。

- MIDI ファイルはバイナリを置かず、`conftest.py` の fixture が `mido` で
  組み立てる（`mk_midi_file` / `rich_midi_file`）
- `pygame.mixer.init()` を通る経路（`Player.play()` / `Player.mk_wav()` /
  `Wav.play()` / CLI の `play`）はテストしない。`Player` は
  `snd_key()` など計算だけ、`Wav` は生成と `save()` まで
- 再生ループ（`Player._play_main()`）も、実時間の待ちに依存するので対象外
- CLI は `click.testing.CliRunner`（サブプロセスを起動しない）
- **loguru のログは pytest の `caplog` に入らない。** ログを確かめる
  テストは `conftest.py` の `log_messages` fixture を使う
  （シンクを張り、`(水準の名前, メッセージ)` のリストに集める）
- **CLI のテストは `mylog.loggerInit()` を通るのでシンクが増える。**
  残ると以降のテストの出力に混ざるため、`conftest.py` の autouse
  fixture が毎回 `logger.remove()` している

すべてのサブコマンドに `-d` / `--debug` があり、loguru のレベルを
DEBUG に切り替える。挙動の調査は基本これで足りる。

## アーキテクチャ

データは `Parser` → dict → `Player` の一方向に流れる。この dict が
モジュール間の唯一の契約:

```python
parsed_data = {
    'channel_set': set[int],       # 元ファイルに含まれる全チャンネル番号
    'note_info': list[NoteInfo],   # velocity > 0 のみ、end_time 設定済み
}
```

- `midi_parser.py` — `Parser.parse()` が3段階で処理する。
  1. `parse1()`: 全トラックを `mido.merge_tracks()` で1本に合成し、
     `set_tempo` を追跡しつつ tick を絶対秒 (`abs_time`) に変換。
     この時点では note_on/note_off が別々の `NoteInfo` として並ぶ。
     `channel_set` はチャンネル絞り込み**前**に集める（フィルタしても
     元ファイルの全チャンネルが分かるようにするため）。
  2. `set_end_time()`: (channel, note) をキーに開始待ちスタックを持ち、
     対応する note_off の時刻を開始側エントリの `end_time` に書き戻す。
     閉じられなかった note は最終イベント時刻で打ち切る。
  3. velocity == 0 のエントリを捨てる。
  `mk_visual()` / `print_visual()` は解析結果のテキスト可視化（`parse -v`）で、
  再生経路とは独立。チャンネルは `A-Z`(開始) / `a-z`(終了) の文字で表す。
- `midi_player.py` — `Player.play()` は再生前に `mk_wav()` で**必要な音を
  全部先に生成してキャッシュする**。キャッシュキーは `(note, 丸めた長さ)` で、
  長さは 0.02 秒単位に丸めて種類数を抑えている（`snd_key()`）。
  再生ループはメインスレッドが `time.sleep()` でスケジューリングし、
  実際の発音は `queue.Queue` 経由でワーカースレッドが行う。`clock_delay`
  （理想時刻と実時刻の差）を次の sleep から引くことで累積ずれを補正する。
- `wav_utils.py` — `Wav` が numpy で sin波を生成。前後にフェードを掛けて
  クリックノイズを消しているのが要点（この処理を外すとブツブツ鳴る）。
  再生は pygame の `sndarray`。
- `midi_utils.py` — `note2freq()`（A4=440Hz, note 69 基準）と関連定数。
- `mylog.py` — loguru の薄いラッパー。`loggerInit()` が出力先と水準を
  決め、`exmsg()` が例外を1行の文字列にする。**`ytstreetorgan` /
  `tmr` と同一のファイル**なので、直すときは他のプロジェクトも揃える
  （TODO-007）。

pygame の mixer はモノラル (`channels=1`) で初期化する。`Player` と
`WavApp` がそれぞれ `pygame.mixer.init()` を呼ぶ。

`__main__.py` は click の group。各サブコマンドは先頭で
`loggerInit(debug)` を呼び（出力先を決めるのはアプリ側の仕事）、
`MidiApp` / `WavApp` / `TransposeApp` を生成して
`main()` → `finally: end()` の形で呼ぶ。

## 慣習

- コードとコメントは既存スタイルに合わせる。docstring は numpy スタイル、
  コメント・ドキュメントは日本語。型ヒントは全モジュールに付いており、
  新規コードでも省略しない。
- ログは `from loguru import logger` して `logger` を直接使う。書式は
  `%s` ではなく `{}`（`logger.debug('rate={}', rate)`）。クラスごとの
  ロガー（`self._log`）は持たない。
- 各クラスは `debug=` をコンストラクタで受けて `self._dbg` に持つが、
  **ログの水準を決めるのは `mylog.loggerInit()` だけ**で、この引数は
  水準に影響しない（loguru は logger ごとの水準を持てない）。利用側の
  互換のために残してある（TODO-007）。
- バージョンは `hatch-vcs` により git タグから決まる。手書きの
  バージョン文字列は無い。
- 公開 API は `__init__.py` の `__all__` が定義する。新しく公開する
  クラス/関数はここに追加する。

## git

作業ブランチは `develop`。`master` はリリース用。

**push はしない。** commit までは行ってよいが、リモートへ反映するかどうかは
ユーザーが判断する。

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) 形式。
件名は英小文字の type で始め、**本文・件名とも日本語**で書く。

```
<type>: <件名。命令形・現在形で簡潔に>

<本文。何を変えたかではなく「なぜ」を書く。72文字程度で折り返す>

- 箇条書きで個別の変更点
```

使う type:

| type | 用途 |
|---|---|
| `feat` | 機能の追加 |
| `fix` | バグ修正 |
| `refactor` | 挙動を変えない内部改善 |
| `docs` | ドキュメントのみ |
| `test` | テストのみ |
| `chore` | 依存更新、ビルド設定など |

破壊的変更は `feat!:` のように `!` を付け、本文に `BREAKING CHANGE:` を書く。

**注意:** `4bd49e8` 以前の履歴は `UPD:` / `ADD:` という独自形式なので、
既存コミットを真似しないこと。

## 注意点

- `pyproject.toml` の依存に `sounddevice` があるが、現状コードからは
  未使用（再生は pygame 経由）。
- カバレッジは `Player` の再生経路を除外しているぶん低く出る（全体で
  8割程度）。**数値を上げるために再生をテストしない**（上の方針を参照）。

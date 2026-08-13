# TODO-025. ドキュメントを実装に合わせる

- [x] `docs/REFERENCE.md` の食い違いを直す
- [x] `CLAUDE.md` の食い違いを直す
- [x] 3 か所に同じ食い違い（`time.sleep()` / `threading.Event.wait()`）を直す
- [x] `loggerInit(out=)` の型の食い違いをどちらに揃えるか決める
- [x] 非公開の型別名をリファレンスに載せるかどうか決める

モデル / effort: Sonnet / medium

## きっかけ

TODO-016 〜 TODO-024 の一連のリファクタで実装が変わったのに、
`docs/REFERENCE.md` と `CLAUDE.md` の記述が追従していない箇所が
複数見つかった。

## 決めたこと

- `docs/REFERENCE.md` 8 章の `loggerInit(out='app.log')` の例
  （`out: TextIO` と食い違う）→ **文書を型に合わせる。** 開いた
  file-like を渡す例に変更した（`mylog.py` は `ytstreetorgan` / `tmr`
  と同一のファイルなので、型を広げる側は選ばなかった。TODO-007）
- 非公開の型別名（`ChannelFilter` / `MidiSource` / `MidiDest`）
  → **リファレンスに載せる。** `parse()` / `transpose_file()` / `write()`
  のシグネチャで型別名を使い、公開 API ではない旨を添えた

## やったこと

`docs/REFERENCE.md`:

- 5.3 の `mk_wav()` / `snd_key()` の引数を実装に合わせた
  （`sec_min` / `sec_max` は TODO-022 で外れている）
- 5.3 の丸めの単位を、0.5 秒を境に 0.02 / 0.01 秒単位と書いた
- `init_mixer()` / `quit_mixer()` を 1 章の import 例、7.1、10 章の表に
  足した。7.1 の例を生の `pygame.mixer.init()` から差し替えた
- 7.4 の `__version__` の例を、具体的な番号を書かない形にした
- 7.1 に `Wav.mk_wav()` の `ValueError`（TODO-017）を足した
- 5.1・7.1 の再生ループの説明を `threading.Event.wait()` に直した
  （TODO-020）
- 8 章の `loggerInit(out=)` の例を型に合わせた
- `parse()` / `transpose_file()` / `write()` に型別名
  （`ChannelFilter` / `MidiSource` / `MidiDest`）を使い、
  非公開である旨を添えた

`CLAUDE.md`:

- アーキテクチャの一覧に `midi_writer.py` を足した
- 「`Player` と `WavApp` がそれぞれ `pygame.mixer.init()` を呼ぶ」を
  「どちらも `wav_utils.init_mixer()` 経由」に直した
- 「各サブコマンドは先頭で `loggerInit(debug)` を呼び」を
  「`run_app()` が共通で行う」に直した（TODO-018）
- `midi_utils.py` の説明に `clip_range()` と `DRUM_CHANNEL`
  （TODO-023 で移した）を足した
- 再生ループの説明を `threading.Event.wait()` に直した（TODO-020）

`src/ytmidilib/midi_player.py`:

- `_play_main()` の docstring を `time.sleep()` から
  `threading.Event.wait()` に直した（コードの変更は無い）

## テスト

```
uv run pytest                    # 128 passed
uv run ruff check src/ tests/    # All checks passed!
uv run mypy src/ tests/          # Success: no issues found in 18 source files
uv run basedpyright              # 0 errors, 0 warnings, 0 notes
```

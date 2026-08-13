# TODO-018. CLI の定型処理と、重複した小さな処理をまとめる

- [x] 4 つのサブコマンドで繰り返している形を 1 か所にまとめる
- [x] `loggerInit()` が二重に呼ばれるのを整理する
- [x] click のコマンド関数に引数の型注釈を付ける
- [x] 範囲に丸める処理（3 か所）
- [x] pygame mixer の初期化 / 終了（2 か所）
- [x] パスと file-like の分岐（`midi_writer.py` に 3 か所）
- [x] `play_sound()` の音量計算の数値に名前を付ける

モデル / effort: Sonnet / medium

## きっかけ

全体を読み直して洗い出したリファクタリングの残り 3 項目のうちの 2 番目
（017 は決着済み）。mixer の初期化が `__main__.py` と `midi_player.py`
にまたがっていて CLI の整理と同じ範囲を触るため、まとめて 1 項目にした。

- `__main__.py` の `parse` / `play` / `wav` / `transpose` は、どれも
  `loggerInit(debug)` → `logger.debug(...)` → `app = ...App(...)` →
  `try: app.main() finally: app.end()` の形を繰り返していた
- `cli` group でも `loggerInit(debug)` を呼んでいたので、サブコマンドを
  実行すると 2 回初期化されていた
- click のコマンド関数は戻り値にしか型注釈が無かった
- `min(max(...))` で範囲に丸める処理が `Player.within_range()` /
  `Wav.play()`（音量） / `midi_writer._shift_note()`（ノート番号）の
  3 か所にあった
- `pygame.mixer.init(frequency=..., channels=1)` / `quit()` が
  `Player.init_mixer()`/`close()` と `WavApp.main()`/`end()` の
  2 か所にあった
- `midi_writer.py` の `isinstance(x, (str, os.PathLike))` による分岐が
  `transpose_file()` に 2 つ（読み/書き）、`write()` に 1 つあった
- `play_sound()` の `snd.set_volume(note_info.velocity / 128 / 8)` の
  128 も 8 も説明が無かった

## 決めたこと

共通化したものをどこに置くか。`within_range()` は `Player` の公開
staticmethod でテストもあるので、移すなら呼び出し側の互換を考える。
→ **`midi_utils.py` に共通関数を作り、`Player.within_range()` はそれを
呼ぶ薄いラッパーにする。** 既存の公開 staticmethod・テストはそのまま
残した。

## やったこと

### CLI の定型処理

- `__main__.py` に `App` Protocol（`main()` / `end()` を持つ）と
  `run_app(ctx, debug, make_app)` を追加し、4 サブコマンドがこれを
  呼ぶだけの形にした
- **App の生成は `loggerInit()` の後に行うファクトリ渡しにした。**
  最初、`app = ...App(...)` を先に作ってから `run_app()` に渡す形で
  実装したところ、コンストラクタ内の `logger.debug(...)` が
  `loggerInit()` より前に走ってしまい、`--debug` を指定しなくても
  DEBUG ログが出る不具合になった（手動での動作確認で発覚）。
  `run_app()` に `Callable[[], App]`（ラムダ）を渡し、
  `loggerInit()` の後で呼ぶ形に直した
- `cli` group での `loggerInit(debug)` 呼び出しをやめ、`run_app()`
  側だけで呼ぶようにした。`cli` group はサブコマンドが無いとき
  ヘルプを出すだけで、ログは使っていないため
- click のコマンド関数（`cli` / `parse` / `play` / `wav` /
  `transpose`）の引数に型注釈を付けた

### 重複の共通化

- `midi_utils.py` に `clip_range()`（PEP 695 の型パラメータ構文で
  int/float どちらでも同じ型を返す）を追加し、
  `Player.within_range()` / `Wav.play()` / `midi_writer._shift_note()`
  から呼ぶようにした
- `wav_utils.py` に `init_mixer(rate)` / `quit_mixer()` を追加し、
  `Player.init_mixer()`/`close()` と `WavApp.main()`/`end()` から
  呼ぶようにした。`__init__.py` の `__all__` にも追加した
- `midi_writer.py` に `_load_midi(src)` / `_save_midi(midi_obj, dst)`
  を追加し、`transpose_file()` の読み書きと `write()` の書きから
  呼ぶようにした
- `Player` に `VELOCITY_MAX = 128` / `VOLUME_ATTENUATION = 8` を足し、
  `play_sound()` の音量計算に名前を付けた

## テスト

既存のテストがそのまま通ることを確認した上で、CLI の実際の動作を
手動で確認した。

- `ytmidilib wav 440 -t 0.5 -n`（`--debug` 無し）で DEBUG ログが出ない
  ことを確認（上記の不具合の再発防止）
- `ytmidilib wav -d 440 -t 0.5 -n` で DEBUG ログが出ることを確認
- `ytmidilib wav 440 -t 0.0000001 -n` で TODO-017 の `ValueError` が
  正しく伝播することを確認
- `ytmidilib parse` で MIDI ファイルの解析が動くことを確認

4 つとも通っている（128 件成功、エラー 0・警告 0）。

```
uv run pytest                    # 128 passed
uv run ruff check src/ tests/    # All checks passed!
uv run mypy src/ tests/          # Success: no issues found in 18 source files
uv run basedpyright              # 0 errors, 0 warnings, 0 notes
```

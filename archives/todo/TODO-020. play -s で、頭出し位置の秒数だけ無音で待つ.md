# TODO-020. `play -s` で、頭出し位置の秒数だけ無音で待つ

- [x] 頭出しの後、最初の音がすぐ鳴るようにする
- [x] 飛ばした後でも `FIRST_DELAY_MAX` の頭打ちが効くようにする
- [x] テストを足すか決めて、決めたとおりにする

モデル / effort: Sonnet / medium

## きっかけ

全体をあらためて読み直して洗い出した項目のうち、唯一のバグ
（他の 4 件はリファクタリング）。

`midi_player.py` の `_play_main()` は、`abs_time` の初期値が `0.0` の
まま `pos_sec` 未満の note を `continue` で飛ばしていた。飛ばした分だけ
`abs_time` が置き去りになるので、最初に鳴らす音の `delay` が
「頭出しの位置そのもの」になっていた。

```python
abs_time = 0.0
for i, note_info in enumerate(data):
    if note_info.abs_time < pos_sec:
        continue                          # abs_time は 0.0 のまま
    delay = note_info.abs_time - abs_time  # = 頭出しの位置
```

長すぎる待ちを `FIRST_DELAY_MAX`（3 秒）で頭打ちにする処理も `i == 0`
で判定していたため、飛ばした後（`i > 0`）には効いていなかった。

`play_sound()` を差し替えて `_play_main()` を直接呼び、実測して確認した
（音声デバイスは要らない）。note を 0.0 / 1.0 / 2.0 / 2.2 秒に置き、
`pos_sec=2.0` で呼んだ結果:

```
delay=2.0
elapsed = 2.70 sec   （鳴っている 0.2 秒 + 余韻 0.5 秒 = 約 0.7 秒のはず）
```

## 決めたこと

テストを足すか。→ **足さない。** テストの方針で「再生ループは実時間の
待ちに依存するので対象外」としているのを優先し、バグ修正のみ行う。

## やったこと

- `abs_time` の初期値を `0.0` から `pos_sec` に変える。頭出し後、最初に
  鳴らす音の `delay` は `note_info.abs_time - pos_sec` になり、
  `pos_sec` そのものを待つことがなくなる
- `FIRST_DELAY_MAX` の頭打ち判定を、配列の添字 `i == 0` ではなく
  「実際に鳴らす最初の note か」を表すフラグ `first_play` に変える。
  これで頭出しで飛ばした後の最初の note にも頭打ちが効く

```python
abs_time = pos_sec
...
first_play = True
for i, note_info in enumerate(data):
    ...
    if note_info.abs_time < pos_sec:
        continue
    delay = note_info.abs_time - abs_time
    if first_play and delay > self.FIRST_DELAY_MAX:
        ...
        delay = self.FIRST_DELAY_MAX
    first_play = False
```

## テスト

`play_sound()` を no-op に差し替えて `_play_main()` を直接呼び、修正前と
同じ条件（note を 0.0 / 1.0 / 2.0 / 2.2 秒、`pos_sec=2.0`）で手動確認した。
`delay=0.0` で即座に鳴り始め、経過時間も約 0.7 秒（鳴っている 0.2 秒 +
余韻 0.5 秒）になった。この確認スクリプトはコミットには含めない。

```
uv run pytest                    # 128 passed
uv run ruff check src/ tests/    # All checks passed!
uv run mypy src/ tests/          # Success: no issues found in 18 source files
uv run basedpyright              # 0 errors, 0 warnings, 0 notes
```

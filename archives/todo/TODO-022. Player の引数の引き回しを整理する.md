# TODO-022. `Player` の引数の引き回しを整理する

- [x] `sec_min` / `sec_max` の持たせ方を決めて、決めたとおりにする
- [x] `play_th()` の `if not note_info` を `is None` にする
- [x] `play_th()` の、debug ログのためだけの時刻計算を見直す
- [x] `WavApp.__init__()` の `print()` を `main()` へ移す

モデル / effort: Sonnet / medium

## きっかけ

`sec_min` / `sec_max` は `play()` で 1 度決まる値なのに、`snd_key()` /
`mk_wav()` / `play_sound()` / `play_th()` / `_play_main()` の 5 つが
受け取って下へ渡すだけになっていた。

`play_th()` の終了判定 `if not note_info:` は `is None` の意図だったが、
`NoteInfo` に `__bool__` は無いので動きは同じでも読んで分かる形では
なかった（TODO-016 で `set_end_time()` の `if ent:` を直したのと同じ
種類）。同じメソッドの `my_clock_base` / `now` は、debug ログに出す
以外に使っていなかった。

`WavApp.__init__()` は、`-m` のときに周波数への変換結果を `print()`
していた。コンストラクタの副作用なので `main()` の方が収まりが良い。

## 決めたこと

- `sec_min` / `sec_max` の持たせ方 → **インスタンス属性にする。**
  `play()` で `self._sec_min` / `self._sec_max` に設定し、以降は
  各メソッドが引数を受け取らず参照する
- `snd_key()`（公開メソッドで、テストも引数付きで呼んでいた）の扱い →
  **引数を消してインスタンス属性を参照する形にする。** テスト側を
  新しい呼び出し方に書き換える

## やったこと

- `Player.__init__()` で `self._sec_min = self.SEC_MIN` /
  `self._sec_max = self.SEC_MAX` を既定値として持たせ、`play()` の中で
  渡された `sec_min` / `sec_max` を書き込む
- `snd_key()` / `mk_wav()` / `play_sound()` / `play_th()` /
  `_play_main()` から `sec_min` / `sec_max` の引数を削除し、
  `self._sec_min` / `self._sec_max` を参照する形にした
- `play_th()` の `if not note_info:` を `if note_info is None:` にした
- `play_th()` の `my_clock_base` / `now` の計算を削除し、debug ログは
  `note_info` だけを出す形にした（実際の時刻表示は `_play_main()` 側の
  ログで賄えている）
- `WavApp.__init__()` から `print()` を除き、`-m` のときの MIDI ノート
  番号を `self._midi_note` に保持。`main()` の先頭で
  `self._midi_note is not None` を見て print するようにした

## テスト

`tests/test_midi_player.py` の `snd_key()` 呼び出しから
`Player.SEC_MIN, Player.SEC_MAX` の引数を除いた（新しいシグネチャに
合わせて書き換え、テスト方針・カバレッジは変えていない）。

```
uv run pytest                    # 128 passed
uv run ruff check src/ tests/    # All checks passed!
uv run mypy src/ tests/          # Success: no issues found in 18 source files
uv run basedpyright              # 0 errors, 0 warnings, 0 notes
```

`WavApp` の `print()` 移動は `uv run ytmidilib wav 60 OUT -m -n` を
手動実行し、`MIDI note: 60 -> freq = 261.626 Hz` が変わらず出ることを
確認した。

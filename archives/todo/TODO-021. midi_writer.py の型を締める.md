# TODO-021. `midi_writer.py` の型を締める

- [x] `write()` の `dict[str, Any]` を無くす
- [x] 繰り返している「パスまたは file-like」の型に別名を付ける

モデル / effort: Sonnet / medium

## きっかけ

`write()` は、並べ替えのために `(tick, 消音が先, note, メッセージの中身)`
というタプルを作っていて、最後の要素が `dict[str, Any]` になっていた。

```python
events: list[tuple[int, int, int, dict[str, Any]]] = []
```

TODO-016 で `dict[str, Any]` を潰した方針の取り残しだった。

`str | os.PathLike[str] | BinaryIO` は `_load_midi()` / `_save_midi()` /
`transpose_file()`（src と dst）/ `write()` の 5 か所に書かれていた。

## 決めたこと

読み込み用と書き出し用で型別名を分けるか。→ **分ける。** `MidiSource`
（読み込み元）と `MidiDest`（書き込み先）に分け、各関数の docstring が
既に「入力」「出力」と区別している意味を型でも表せるようにした。

## やったこと

- `type MidiSource = str | os.PathLike[str] | BinaryIO` と
  `type MidiDest = str | os.PathLike[str] | BinaryIO` を PEP 695 の
  `type` 文で定義し、`_load_midi()` / `_save_midi()` /
  `transpose_file()` / `write()` の該当引数に適用した
- `write()` の `events` を `dict[str, Any]` の代わりに `mido.Message` を
  その場で組み立てて持つ形にした（並べ替えのキーは `e[0], e[1], e[2]`
  だけを見ているので、メッセージ同士を比較することにはならない）
- `track.append()` の直前で tick の delta を time に反映する処理は、
  `msg.time = ...` の属性代入ではなく `msg.copy(time=...)` にした。
  `mido.Message` は `vars(self).update(...)` で属性を持たせているため
  mypy（`follow_untyped_imports`）が動的な属性代入を追跡できず
  `has no attribute time` と誤検知した。`copy()` は明示的なメソッドとして
  定義されているため誤検知しない

## テスト

```
uv run pytest                    # 128 passed
uv run ruff check src/ tests/    # All checks passed!
uv run mypy src/ tests/          # Success: no issues found in 18 source files
uv run basedpyright              # 0 errors, 0 warnings, 0 notes
```

`midi_writer.py` の既存テストが `write()` / `transpose_file()` を
カバレッジ 100% で通しているため、新規テストは足さなかった。

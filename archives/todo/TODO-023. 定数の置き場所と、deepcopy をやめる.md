# TODO-023. 定数の置き場所と、`deepcopy` をやめる

- [x] `DRUM_CHANNEL` を `midi_utils.py` へ移す
- [x] `set_end_time()` の `copy.deepcopy` をやめる
- [x] 繰り返している「絞り込むチャンネル」の型に別名を付ける

モデル / effort: Sonnet / low

## きっかけ

`DRUM_CHANNEL`（9）は `midi_writer.py` にあったが、MIDI 仕様の定数で、
`__main__.py`（`--drums` のヘルプ）と `tests/conftest.py` からも使って
いた。`DEFAULT_TEMPO` を `midi_utils.py` へ移したのと同じ理由が当てはまる
（TODO-016）。

`set_end_time()` の `copy.deepcopy(in_data)` は、スカラーしか持たない
`NoteInfo` には過剰。5 万音で実測:

```
deepcopy    : 0.284 sec
replace()   : 0.077 sec
```

`list[int] | tuple[int, ...] | None` は `midi_parser.py` の `parse1()` /
`parse()` と、`Parser` の同名メソッドの 4 か所にあった。TODO-021 と同じく
`type` 文で別名を付けられる。

## やったこと

- `DRUM_CHANNEL` を `midi_writer.py` から `midi_utils.py` へ移した。
  `midi_writer.py` は `from .midi_utils import ... DRUM_CHANNEL` で参照
  する側になった。`__init__.py` のインポート元と `__all__` の並びも
  `midi_utils` 側に追随させた（`docs/REFERENCE.md` の記述はどちらの
  モジュール由来かに触れていなかったので変更不要だった）
- `set_end_time()` の `copy.deepcopy(in_data)` を
  `[dataclasses.replace(ni) for ni in in_data]` に変えた。`NoteInfo` は
  スカラーのフィールドしか持たないので浅いコピーで十分。50000 件で
  実測すると約 0.10 秒（`deepcopy` の実測値 0.284 秒より速い）
- `midi_parser.py` に `type ChannelFilter = list[int] | tuple[int, ...] | None`
  を追加し、`parse1()` / `parse()` と `Parser.parse1()` /
  `Parser.parse()` の `channel` 引数の型をこれに揃えた

## テスト

```
uv run pytest                    # 128 passed
uv run ruff check src/ tests/    # All checks passed!
uv run mypy src/ tests/          # Success: no issues found in 18 source files
uv run basedpyright              # 0 errors, 0 warnings, 0 notes
```

既存のテストが `set_end_time()` / `DRUM_CHANNEL` の挙動をカバーしている
ため、新規テストは足さなかった。

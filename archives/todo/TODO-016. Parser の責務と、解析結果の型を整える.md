# TODO-016. `Parser` の責務と、解析結果の型を整える

- [x] `self._channel_set` を持つのをやめる
- [x] self を使わないメソッドの置き場所を決める
- [x] 可視化を別モジュールに分けるか決める
- [x] `set_end_time()` の「最終イベント時刻」の求め方を明示的にする
- [x] `mk_event_list()` の戻り値に型を付ける
- [x] `VisualData['data']` に型を付ける
- [x] `NoteInfo` を dataclass にするか決めて、決めたとおりにする
- [x] `DEFAULT_TEMPO` を適切なモジュールへ移し、`__all__` に足す
- [x] `conftest.py` の `DEFAULT_TEMPO` の import を公開 API 経由にする

モデル / effort: Opus / high

## きっかけ

全体を読み直して洗い出したリファクタリングの 5 項目のうちの 2 番目。
受け渡しのデータ構造そのものなので、ここが決まらないと TODO-018 の
CLI 側も揺れる、という順で並べてあった。

- `Parser` は `parse()` の中で `self._channel_set` に代入しているが、
  同じものを戻り値にも入れていて冗長。外から読む手段も無かった
- `parse1()` / `set_end_time()` / `mk_event_list()` / `mk_visual()` は
  `self._dbg` 以外に self を使っていない
- 可視化は `parse -v` 専用で、再生経路とは独立している
- `set_end_time()` の末尾の `if ent:` は、ループ変数の残り（最後の
  エントリ）を「最終イベント時刻」として使っていて、読んで分からない
- `mk_event_list()` の戻り値と `VisualData['data']` が
  `list[dict[str, Any]]` で、イベントの構造がコードから読めない
- `end_time` が `None` のままの `NoteInfo` を `mk_event_list()` に渡すと、
  `sorted()` が `None` との比較で `TypeError` になった
- `DEFAULT_TEMPO` が `midi_parser.py` にあり、`__all__` にも無いため、
  `tests/conftest.py` が内部モジュールを直接読んでいた

## 決めたこと

着手時に 4 点を確認した（いずれも推奨案のとおり）。

| 決めること | 決めたこと |
|---|---|
| 可視化を分けるか | `midi_visual.py` に分け、`Parser` にはメソッドを委譲として残す |
| self を使わないメソッド | モジュールレベルの関数を本体にし、`Parser` は委譲だけ |
| `NoteInfo` を dataclass にするか | する |
| `mk_event_list()` に `end_time=None` が来たら | `write()` と同じく長さ 0 として扱う |

**メソッドを委譲として残したのは、`ytstreetorgan` が
`Parser.mk_visual()` / `Parser.print_visual()` をメソッドとして
呼んでいるため**（`src/ytstreetorgan/apps.py`）。消すと、あちらの
修正（要求書・回答書のやり取り）が必要になる。なお `ytstreetorgan` は
`ytmidilib` を git のタグ `0.3.0` で固定しているので、タグを上げるまで
影響は無い。

`NoteInfo` は dataclass にすると **ハッシュ可能でなくなる**（`__eq__` が
付くため `__hash__` が `None` になる）。両プロジェクトとも `set` や
dict のキーには使っていないことを確かめてから決めた。引数の順序と
名前は変えていないので、位置引数・キーワード引数のどちらの呼び方も
そのまま動く。

## やったこと

- `self._channel_set` をやめ、`parse()` のローカル変数にした
- `parse1()` / `set_end_time()` / `parse()` / `mk_event_list()` を
  モジュールレベルの関数にし、`Parser` は委譲だけにした。
  メソッドの中からの名前解決にクラスの名前空間は入らないので、
  同名でも再帰にはならない（コメントで明記した）
- 可視化（`mk_visual()` / `format_visual()` / `print_visual()` と
  `V_CHR_*`）を `midi_visual.py` に分けた。`Parser` の委譲メソッドは、
  `midi_visual` → `midi_parser` の import と循環しないよう、
  メソッドの中で import する。`VisualData` の型注釈は
  `TYPE_CHECKING` の import と文字列で書いた
- `Parser.MIDI_NOTE_N`（128）は `midi_utils.NOTE_N` と重複していたので、
  移す際に `NOTE_N` に統一した（外から参照されていないことを確認済み）
- `set_end_time()` の最終イベント時刻を `max(ent.abs_time for ...)` で
  求め、空リストは先に返すようにした
- `NoteInfo` を dataclass にし、丸めを `__post_init__` へ移した。
  ついでに `__str__()` の `if self.end_time:` を `is not None` にした
  （`end_time` が 0.0 のとき end が出なかった）
- `NoteEvent` / `TimedEvent` / `VisualLine` を `TypedDict` で定義した。
  `mk_visual()` は行を組み立てる途中で `chr` が `list[str]` に
  なっていたので、組み立て用のローカル変数を分けた
- `end_time` が `None` の音は、`write()` と同じく長さ 0 として扱う
- `DEFAULT_TEMPO` を `midi_utils.py` へ移し、`__init__.py` の `__all__`
  に足した。`midi_writer.py` と `tests/conftest.py` の import も直した
- `__all__` に、モジュールレベルの関数と新しい型を足した
  （`parse` / `mk_event_list` / `mk_visual` / `format_visual` /
  `print_visual` / `NoteEvent` / `TimedEvent` / `VisualLine` /
  `DEFAULT_TEMPO`）。`parse1()` / `set_end_time()` は `parse()` の
  内部の段階なので、公開 API には入れていない
- `__main__.py` の可視化の呼び出しを、委譲メソッドではなく
  `midi_visual` の関数に切り替えた
- CLAUDE.md / docs/REFERENCE.md / README.md を追随させた。
  リファレンスマニュアルの例は `Parser().parse()` から `parse()` に
  書き換え、`Parser` は「以前のコードのために残してある」と書いた

## テスト

- 可視化のテストを `tests/test_midi_visual.py` に分けた
- `tests/test_midi_parser.py` はモジュールレベルの関数を直接呼ぶ形に
  書き換え、`Parser` の委譲を確かめるテストを足した
- 足したテスト: `NoteInfo` の比較・キーワード引数・`end_time` が 0.0 の
  `__str__()`、`set_end_time([])`、`mk_event_list()` に `end_time=None`、
  `mk_visual([])`、`Parser` の委譲（`midi_parser` / `midi_visual` の両方）
- `NoteInfo` が比較できるようになったので、`test_parse` は属性を並べる
  形から `NoteInfo` のリストとの比較に変えた

4 つとも通っている（125 件成功、エラー 0・警告 0）。

```
uv run pytest                    # 125 passed
uv run ruff check src/ tests/    # All checks passed!
uv run mypy src/ tests/          # Success: no issues found in 18 source files
uv run basedpyright              # 0 errors, 0 warnings, 0 notes
```

`ytstreetorgan` のテスト 297 件も、`PYTHONPATH` でこの版を読ませて
通ることを確かめた（あちらは `0.3.0` 固定なので、タグを上げるときの
確認になる）。

CLI も `ytmidilib parse -v` で表示を確かめた。

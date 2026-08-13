# TODO-024. `click_utils.py` / `mylog.py` に型注釈を付ける

- [x] 3 プロジェクトを揃えるかどうかを決める
- [x] 型注釈を付ける

モデル / effort: Sonnet / medium

## きっかけ

CLAUDE.md には「型ヒントは全モジュールに付いている」と書いてあったが、
実際には次が未注釈だった:

- `click_utils.py` の `click_common_opts()` の戻り値、内側の
  `_decorator(func)` の引数と戻り値
- `mylog.py` の `loggerInit()` の `out=sys.stderr`、`exmsg()` の `ex`

この 2 ファイルは `ytstreetorgan` / `tmr` と同一のファイルなので、直すと
3 プロジェクトで揃える必要が生じる（TODO-007 / TODO-014）。

## 決めたこと

- 3 プロジェクトを同時に直すか → **ytmidilib だけ直し、他の 2 つ
  （`ytstreetorgan` / `tmr`）は別途行う。** この場ではリポジトリの外に
  出ないようにした
- デコレータの型 → **`Callable[..., Any]` で済ませる。** `click` の
  デコレータ自体、この 2 ファイルでは型情報として扱っていない
  （`ignore_missing_imports` / `follow_untyped_imports` の対象）ため、
  `ParamSpec` で厳密にしても実益が薄いと判断した

## やったこと

- `click_utils.py`:
  `click_common_opts()` の戻り値を
  `Callable[[Callable[..., Any]], Callable[..., Any]]` に、
  内側の `_decorator(func: Callable[..., Any]) -> Callable[..., Any]` に
  型を付けた
- `mylog.py`:
  `loggerInit()` の `out=sys.stderr` を `out: TextIO = sys.stderr` に、
  `exmsg(ex)` を `exmsg(ex: Exception) -> str` にした

`ytstreetorgan` / `tmr` 側の同期は、この場では行っていない
（TODO-007 / TODO-014 と同じ扱い）。

## テスト

```
uv run pytest                    # 128 passed
uv run ruff check src/ tests/    # All checks passed!
uv run mypy src/ tests/          # Success: no issues found in 18 source files
uv run basedpyright              # 0 errors, 0 warnings, 0 notes
```

`uv run ytmidilib --help` / `uv run ytmidilib wav --version` を手動実行し、
共通オプション（`--help` / `--version` / `--debug`）が変わらず動くことを
確認した。

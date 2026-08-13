# TODO-014. `click_utils.py` を導入する

## きっかけ

`src/ytmidilib/click_utils.py` は先に置かれていた（`3b7007c`）が、
まだどこからも使われていなかった。`ytstreetorgan` / `tmr` と共有する
ファイルで、`click_common_opts()` が `--version` / `--debug` / `--help`
をまとめて付けるメタデコレータになっている。これを `__main__.py` の
各コマンドに載せ、共通オプションの定義を 1 か所にまとめる。

立てたときの覚書は「オプションがコンフリクトする場合は個別に判断」の
1 行だけだったので、着手前に衝突を洗い出して方針を確定させた。

## やったこと

`src/ytmidilib/__init__.py`:

- `__version__` を追加した。`importlib.metadata.version()` で読む
  （バージョンは `hatch-vcs` が git タグから決めるため）。パッケージと
  して入っていなければ `'0.0.0'`、パッケージ外から読み込まれた場合は
  `'_._._'`。`__author__` / `__date__` ともども `__all__` に載せた

`src/ytmidilib/__main__.py`:

- `COMMON_OPTS = click_common_opts(__version__, use_v=False)` を 1 度だけ
  作り、`cli` / `parse` / `play` / `wav` / `transpose` の 5 つに付けた
- `click_common_opts` が `click.pass_context` を含むので、全コマンドの
  第 1 引数を `ctx` にした。`cli` group が持っていた `@click.pass_context`
  は二重になるので外した
- debug の引数名を `dbg` から `debug` へ統一（デコレータ側が固定のため）
- `CONTEXT_SETTINGS`（`help_option_names`）を削除した。`click_common_opts`
  が `click.help_option('-h', '--help')` を明示的に付けるので重複する。
  `TRANSPOSE_CONTEXT_SETTINGS` は `ignore_unknown_options=True` だけを
  残した（`transpose` の `N` に `-2` のような負の値を取るため）
- `cli` group の `loggerInit()` を `loggerInit(debug)` にした。group にも
  `--debug` が付いたため
- 各コマンドの先頭に `logger.debug('command={!r}', ctx.command.name)` を
  足した（`ytstreetorgan` と同じ形）

### `-v` は既存を優先した

`-v` は既に `parse` の `--visual` と `wav` の `--vol` が使っている。
サブコマンドごとに意味が違うと紛らわしいので、**全コマンドで
`use_v=False`** にし、version は `-V` / `--version` だけにした。
`--visual` / `--vol` の短縮形を取り上げる案（`-v` を version に統一）は
破壊的変更になるので採らなかった。

`ytstreetorgan` も `parse` を `use_v=False` にしており、そちらと揃う。

### `click_utils.py` 自体には手を入れていない

`mylog.py` と同じく `ytstreetorgan` / `tmr` と同一のファイルなので、
ytmidilib の慣習（型ヒント必須・numpy スタイル docstring）に合わせると
3 プロジェクトで内容がずれる。現状のままで `ruff` / `mypy` /
`basedpyright` はいずれも通る。直すときは他のプロジェクトも揃える。

### 文書

- `docs/REFERENCE.md` 9 章に共通オプションの表を置き、`-v` を共通に
  含めていない理由を書いた。7.4 として `__version__` の節を足した
- `CLAUDE.md` のモジュール一覧に `click_utils.py` を足し、`__main__.py`
  の説明に `COMMON_OPTS` と `ctx` のことを書いた

## テスト

`tests/test_cli.py` に 7 件追加（110 → 117 passed）。

- `test_version` — `-V` / `--version` が group と全サブコマンドで効く
  （6 パターンの parametrize）。`transpose` は `ignore_unknown_options`
  だが `-V` は既知のオプションなので効くことを、実際に確かめた
- `test_wav_vol` — `wav -v 0.5` が version ではなく音量として扱われ、
  ファイルが書き出される

既存の `test_parse_visual`（`parse -v`）と `test_transpose_negative`
（`transpose ... -2`）は無変更のまま通る。

`pytest` / `ruff` / `mypy` / `basedpyright` の 4 つとも、エラー 0・警告 0。

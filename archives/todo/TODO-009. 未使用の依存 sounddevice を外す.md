# TODO-009. 未使用の依存 `sounddevice` を外す

## きっかけ

`sounddevice` は `pyproject.toml` の依存に入っていたが、コードからは
使われていなかった（再生は pygame 経由）。`CLAUDE.md` にも「依存に
あるが未使用」と注記してあるだけの状態が続いていた。

外す前に、次を確認した。

- `grep` した範囲で `import sounddevice` は無く、参照は
  `pyproject.toml` とドキュメントの注記だけ
- `uv tree` で、他のパッケージからの逆依存も無い（`ytmidilib` の
  直接依存のみ）

## やったこと

- `pyproject.toml` の `dependencies` から `"sounddevice"` を削除
- `uv sync` で `uv.lock` を更新。`sounddevice` が引いていた `cffi` /
  `pycparser` も一緒に消えた（計 3 パッケージ）
- `CLAUDE.md` の「注意点」から、未使用という注記を消し、
  「音の再生は pygame 経由のみ」に書き換えた

`docs/REFERENCE.md`（TODO-008）にも同じ注記を書いていたが、この項目と
同じ流れで消したので、追加されたファイルには最初から入っていない。

## テスト

`CLAUDE.md` の必須 4 項目を全部通した。

```
pytest        108 passed
ruff          All checks passed!
mypy          Success: no issues found in 15 source files
basedpyright  0 errors, 0 warnings, 0 notes
```

加えて、`uv run ytmidilib --help` でサブコマンドが 4 つとも出ることを
確認した（依存を減らしたことで import が壊れていないか）。

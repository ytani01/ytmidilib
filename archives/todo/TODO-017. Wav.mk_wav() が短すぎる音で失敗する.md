# TODO-017. `Wav.mk_wav()` が短すぎる音で失敗する

- [x] `out_len == 0` のときにフェードアウトを掛けないようにする
- [x] サンプル数を整数で求める
- [x] 短い長さ（0 を含む）のテストを足す

モデル / effort: Sonnet / medium

## きっかけ

全体を読み直して洗い出したリファクタリングの残り 3 項目の 1 つ。
`wav_utils.py` の `mk_wav()` は、フェードアウトを
`sin_wave[-out_len:] *= ...` で掛けている。`out_len` が 0 になると
`[-0:]` が**配列全体**を指すため、長さ 0 の配列との演算になって
例外が出ていた。

```
Wav(440, 0.00004, 22050)
-> ValueError: non-broadcastable output operand with shape (1,)
   doesn't match the broadcast shape (0,)
```

`Player` は `SEC_MIN`（0.02 秒）で下限を切るので再生経路では起きないが、
`ytmidilib wav 440 -t 0.00004` では通ってしまっていた。

同じ箇所の `np.arange(self._rate * self._sec)` は float を渡していて、
サンプル数が浮動小数点の丸め任せになっていた。

## 決めたこと

長さ0（サンプルが1つも取れない長さ）を「空の音源」として通すか、
エラーにするか。→ **エラーにする。** 分かりにくい numpy の
ブロードキャストの例外の代わりに、明示的な `ValueError` を出す。

## やったこと

- サンプル数を `int(self._rate * self._sec)` で先に整数として求め、
  `np.arange()` にはその整数を渡すようにした
- サンプル数が 0 以下なら、`mk_wav()` の冒頭で明示的な `ValueError`
  を出すようにした（`Wav.__init__()` から伝播する）
- `out_len > 0` のときだけフェードアウトを掛けるようにガードした。
  これにより、サンプルは取れるがフェードアウトの掛からないほど
  短い音（`out_len == 0`）は、エラーにはせず素通りする

## テスト

- `sec=0.0` / `sec=0.00004`（フェードアウトを掛けると壊れていた値）で
  `ValueError` になることを確認するテストを足した
- サンプル1個分の長さ（フェードアウトは掛からないが、エラーにも
  ならない境界）で成功することを確認するテストを足した

4 つとも通っている（128 件成功、エラー 0・警告 0）。

```
uv run pytest                    # 128 passed
uv run ruff check src/ tests/    # All checks passed!
uv run mypy src/ tests/          # Success: no issues found in 18 source files
uv run basedpyright              # 0 errors, 0 warnings, 0 notes
```

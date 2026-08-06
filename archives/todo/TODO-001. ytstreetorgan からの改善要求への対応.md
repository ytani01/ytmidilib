# TODO-001. `ytstreetorgan` からの改善要求への対応

## きっかけ

出典: `docs/20260806a-ytmidilib-requests.md`（2026-08-06）

要求は 0.0.3 時点のコードに対するもので、その後の
`0e1a2ea refactor: 型ヒントを追加し、lint の指摘を解消する` で
**要求 #2 / #3 / #7 / #13 は既に解消済み**。

以下、`TODO-001-N` が作業単位、`#N` は要求書の項番。

### 守るべき互換性（要求書「互換性の方針」）

要求元が実際に使っているのは次だけ。**ここが壊れなければ、残りは自由に
変えてよい。** 各作業の前後でこの表を確認する。

| API |
|---|
| `Parser()` / `Parser.parse(midi_file, channel)` |
| `Parser.mk_visual()` / `Parser.print_visual()` |
| `NoteInfo`（`abs_time` / `channel` / `note` / `velocity` / `end_time` / `length()` / `__str__`） |
| `Player()` / `Player.play(parsed, pos, sec_min, sec_max)` |
| `Player.DEF_RATE` / `Player.SEC_MIN` / `Player.SEC_MAX` |

特に注意する箇所:

- TODO-001-5: `block` は**既定値付きの追加引数**にする
  （`play(parsed, pos, sec_min, sec_max)` の呼び出しがそのまま通ること）
- TODO-001-9: `print_visual()` を**消さない**。`format_visual()` を足して
  `print_visual()` はその薄いラッパーにする
- TODO-001-4: `Player()` 生成自体は引き続き成功すること
  （音声デバイス不在で `__init__` が失敗するようにしない）
- #4（TODO-001-3）と #7 は出力・戻り値の形が変わるが、要求元はタグ
  `0.0.3` で固定しているので入れてよい

### 対応済み（要求 #2, #3, #7, #13）

現状のコードを確認した結果、追加作業は不要。

- #2 `NoteInfo.end_time` — `None if end_time is None else round(end_time, 3)`
  になっており、`int` も通る（`midi_parser.py:41`）
- #3 型注釈 — 公開 API に注釈あり。既定値 `None` も撤去済み
- #7 戻り値の型 — `TypedDict` を定義済み。
  要求元の文書に合わせて **`ParsedMidi` に改名した**
  （2026-08-06 ユーザー判断）
- #13 `length()` の docstring — `[sec]` に修正済み。
  `end_time is None` で `0.0` を返す旨も追記した

## やったこと

優先度順。TODO-001-1 は先に単独でコミットする。

### TODO-001-1. tempo 既定値 500000 を適用する（#1・不具合・最優先）

- `Parser.parse1()` の `cur_tempo = None` → `cur_tempo = DEFAULT_TEMPO`
  （= 500000。`mido.bpm2tempo(120)`。MIDI 仕様の既定値）
- `if cur_tempo:` の分岐を撤去
- 確認済み: `set_tempo` 無し・480tpb・四分音符の MIDI で `length()` == 0.5、
  `set_tempo` 有りの既存ファイル（pygame の `MIDI_sample.mid`）で
  `parse -v` の出力が変更前と一致

### TODO-001-2. `set_end_time()` の例外処理（#9・不具合）

- `except KeyError` → `except (KeyError, IndexError)`
- 警告メッセージに channel / note / 時刻を含める
- 確認済み: 対応する note_on が無い note_off を含む MIDI で、警告を出して
  読み飛ばし、残りの note は正しく解析される

### TODO-001-3. `Player` の標準出力をやめる（#4・改善）

**方針: `print()` は DEBUG ログに置き換える**（要求の選択肢 1。
コールバック `on_note` は採らない）。

- `play_th()` の `print(f'{now:08.3f} / {note_info}')`（`midi_player.py:134`）
  → `self._log.debug('%08.3f / %s', now, note_info)`
- `play()` 末尾の `print('end music')` → `self._log.debug('end music')`
- 既定（`debug=False`）では標準出力・標準エラーに何も出ない
  - `mk_wav()` 後の `_log.info('len(snd)=...')` も DEBUG へ落とした
- CLI で従来の表示が欲しい場合は `-d` を付ける
- 確認済み: `play` 実行時に `Player` からの出力が無いこと

### TODO-001-4. `pygame.mixer.init()` の遅延化（#5・改善）

- `Player.__init__()` から `pygame.mixer.init()` を外し、`init_mixer()` を
  新設して `mk_wav()` 冒頭で呼ぶ（初期化済みなら何もしない）
- `close()` を追加し、`__enter__` / `__exit__` も付けた
- 音声デバイス不在時は `play()`（`mk_wav()`）で `pygame.error` になる
- `WavApp` も `main()` の再生時のみ初期化するようにし、`end()` で
  `pygame.mixer.quit()`。保存のみ（`-n`）なら音声デバイス不要になった
- `MidiApp.end()` で `Player.close()` を呼ぶ
- 確認済み: `Player()` 生成だけでは mixer が初期化されないこと、
  `with Player()` で初期化 → 終了時に解放されること、
  `parse` / `play` / `wav -n` が従来どおり動くこと

### TODO-001-5. 再生の停止・非同期化（#6・機能追加）

- `stop()` — `threading.Event` を見て、次の音符の前でループを抜ける。
  ワーカースレッドにも終了を伝え、`pygame.mixer.stop()` で鳴っている音も
  止める。待ちは `sleep()` ではなく `Event.wait()` にして反応を良くした
- `play(..., block: bool = True)` — `False` で別スレッド再生。
  音源生成 (`mk_wav()`) は `block` によらず呼び出し側で先に済ませるので、
  音声デバイス不在のエラーは `play()` から見える
- `is_playing() -> bool`
- 再生中の `play()` は `RuntimeError`（`stop()` を先に呼ぶ）
- `stop()` 後に再度 `play()` できること（Event を毎回クリアする）
- 確認済み: 6秒の MIDI で、`block=False` が即座に戻る／1秒で `stop()` でき
  `is_playing()` が False になる／再度 `play()` できる／
  `play(parsed, pos, sec_min, sec_max)` の従来形が 6 秒ブロックする

### TODO-001-6. MIDI 書き出し（#8・機能追加）

- 新規 `midi_writer.py`
  - `write(midi_file, note_info, ticks_per_beat=480, tempo=500000) -> None`
  - `NoteInfo` を note_on / note_off に展開し、絶対秒 → tick へ戻す
    （`mido.second2tick`）。同時刻は消音 → 発音の順に並べ、delta=0 で続ける
    （同じ note の再打鍵と衝突させないため）
  - `transpose(note_info, n) -> list[NoteInfo]`。
    **範囲外は `ValueError`**（2026-08-06 ユーザー判断）。1音でも
    範囲外なら移調全体を失敗させる。元のリストは変更しない
- 確認済み: 和音・同一 note の連打を含むデータで
  `parse()` → `write()` → `parse()` が一致（既定 480/500000 に加え、
  96/300000・960/700000 でも一致）。`transpose(+12)` が元を壊さないこと、
  範囲外で `ValueError` になること
- `__init__.py` の `__all__` に `write` / `transpose` /
  `DEF_TICKS_PER_BEAT` を追加

### TODO-001-7. ロギングをライブラリらしくする（#10・改善）

- `get_logger()` から `addHandler()` / `propagate = False` を外し、
  レベル設定のみにした
- ロガー名を `inspect.stack()` ベースから、パッケージ名 (`ytmidilib.*`)
  ベースへ（`get_logger()` の重さも解消）。`__name__` を渡された場合は
  そのまま使う
- ハンドラの設定は `my_logger.init_handler()` に切り出し、
  `__main__.py` の click group から呼ぶ
- 確認済み: CLI で従来どおりログが出る／`-d` で DEBUG が出る／
  ライブラリとして import しただけではハンドラが付かない／
  アプリ側の `logging.basicConfig()` の書式に従う

### TODO-001-8. パスを `str | os.PathLike[str]` に（#11・改善）

- `Parser.parse()` のシグネチャと docstring。`mido` 側はそのまま通る
- ついでに `Wav.save()` も同様にした（`wave.open()` の型定義が `str`
  しか受けないので `os.fspath()` を挟む）。`midi_writer.write()` は
  最初から `str | os.PathLike[str]`
- 確認済み: `pathlib.Path` で `parse` / `write` / `save` が通る

### TODO-001-9. `format_visual()` の追加（#12・改善）

- `format_visual(v_data, channel_set) -> str` を新設し、
  `print_visual()` はそれを `print()` するだけにした
- `_print_note_ruler()` を `_format_note_ruler()`（`list[str]` を返す）へ
- 確認済み: `parse -v` の出力が変更前と完全一致（diff で確認）

## テスト

当時は `tests/` が無く、一時ディレクトリの使い捨てスクリプトによる手動確認
（各項目の「確認済み」）。のちに [[TODO-006]] で自動テストとして残した。

- `uv run ruff check src/` / `uv run mypy src/` / `uv run basedpyright` を
  すべて通す — 完了（エラー0・警告0）
- 互換性の表の API がすべて通ることを確認 — 完了
- タグ付け — 完了。**`0.1.0`**（#4 の出力変更・#5 の初期化タイミング変更・
  `ParsedMidi` への改名を含むため）
- push はユーザーが行う。Claude は commit まで

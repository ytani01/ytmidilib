# TODO

`docs/20260806a-ytmidilib-requests.md`（`ytstreetorgan` からの要求, 2026-08-06）
への対応整理。要求は 0.0.3 時点のコードに対するもので、その後の
`0e1a2ea refactor: 型ヒントを追加し、lint の指摘を解消する` で
**2 / 3 / 7 / 13 は既に解消済み**。

## 対応済み（要求 #2, #3, #7, #13）

現状のコードを確認した結果、追加作業は不要。

- #2 `NoteInfo.end_time` — `None if end_time is None else round(end_time, 3)`
  になっており、`int` も通る（`midi_parser.py:41`）
- #3 型注釈 — 公開 API に注釈あり。既定値 `None` も撤去済み
- #7 戻り値の型 — `ParsedData(TypedDict)` を定義済み（`midi_parser.py:73`）
  - ただし要求元の文書は `ParsedMidi` という名前を想定している。
    **要判断:** 別名 `ParsedMidi = ParsedData` を足すか、名前を寄せるか、
    このままとするか
- #13 `length()` の docstring — `[sec]` に修正済み。`end_time is None` で
  `0.0` を返す挙動になっているので、docstring にその旨を追記しておくと親切

## やること

優先度順。1 は先に単独でコミットする。

### 1. tempo 既定値 500000 を適用する（#1・不具合・最優先）

- `Parser.parse1()` の `cur_tempo = None` → `cur_tempo = 500000`
  （`mido.bpm2tempo(120)`。MIDI 仕様の既定値）
- `if cur_tempo:` の分岐は不要になるので整理する
- 確認: `set_tempo` 無し・480tpb・四分音符の MIDI で `length()` == 0.5、
  `set_tempo` 有りの既存ファイルで結果が変わらないこと

### 2. `set_end_time()` の例外処理（#9・不具合）

- `except KeyError` → `except (KeyError, IndexError)`（`midi_parser.py:187`）
- 警告メッセージに channel / note / 時刻を含める

### 3. `Player` の標準出力をやめる（#4・改善）

**方針: `print()` は DEBUG ログに置き換える**（要求の選択肢 1。
コールバック `on_note` は採らない）。

- `play_th()` の `print(f'{now:08.3f} / {note_info}')`（`midi_player.py:134`）
  → `self._log.debug('%08.3f / %s', now, note_info)`
- `play()` 末尾の `print('end music')` → `self._log.debug('end music')`
- 既定（`debug=False`）では標準出力・標準エラーに何も出ない
- CLI で従来の表示が欲しい場合は `-d` を付ける

### 4. `pygame.mixer.init()` の遅延化（#5・改善）

- `Player.__init__()` から `pygame.mixer.init()` を外し、`play()` 冒頭
  （または `mk_wav()`）で 1 回だけ初期化する
- `close()` を追加し、`__enter__` / `__exit__` も付ける
- 音声デバイス不在時は `play()` で分かるエラーになること
- 注意: `WavApp` も `pygame.mixer.init()` を呼ぶので、二重初期化の扱いを
  そろえる（初期化済みなら何もしない）

### 5. 再生の停止・非同期化（#6・機能追加）

- `stop()` — `threading.Event` を見て、次の音符の前でループを抜ける。
  ワーカースレッドにも終了を伝える
- `play(..., block: bool = True)` — `False` で別スレッド再生
- `is_playing() -> bool`
- `stop()` 後に再度 `play()` できること（Event を毎回クリアする）

### 6. MIDI 書き出し（#8・機能追加）

- 新規 `midi_writer.py`（仮）
  - `write(midi_file, note_info, ticks_per_beat=480, tempo=500000) -> None`
  - `NoteInfo` を note_on / note_off に展開し、絶対秒 → tick へ戻す
    （`mido.second2tick`）。同時刻イベントの delta=0 の並びに注意
  - `transpose(note_info, n) -> list[NoteInfo]`（範囲外の扱いを決める。
    クリップせず捨てる／例外／飽和のいずれか。**要判断**）
- `parse()` → `write()` → `parse()` の往復で値が一致すること
- `__init__.py` の `__all__` に追加

### 7. ロギングをライブラリらしくする（#10・改善）

- `get_logger()` から `addHandler()` / `propagate = False` を外す。
  レベル設定のみにする
- ロガー名を `inspect.stack()` ベースから `__name__` ベースへ
  （`get_logger()` の重さも解消される）
- ハンドラの設定は `__main__.py` へ移す
- 影響範囲: 全モジュールが `get_logger()` を使っているので、
  CLI で従来どおりログが出ることを確認する

### 8. パスを `str | os.PathLike[str]` に（#11・改善）

- `Parser.parse()` のシグネチャと docstring。`mido` 側はそのまま通る

### 9. `format_visual()` の追加（#12・改善）

- `format_visual(v_data, channel_set) -> str` を新設し、
  `print_visual()` はそれを `print()` するだけにする
- `_print_note_ruler()` も文字列を返す形へ（`_format_note_ruler()`）

## 完了後

- `uv run ruff check src/` / `uv run mypy src/` / `uv run basedpyright` を
  すべて通す（エラー0・警告0 を維持）
- 要求元はタグ `0.0.3` で固定しているので、**新しいタグを打つ**
  （#4 の出力変更・#5 の初期化タイミング変更を含むので、0.1.0 相当）
- push はユーザーが判断する

# TODO-003. MIDI ファイルの移調（要求書 2 通目）

## きっかけ

出典: `archives/20260806c-ytmidilib-requests-2.md`（2026-08-06、対象 0.1.0）

要求は 4 件。**#1（`transpose_file()` の新設）が本体**で、#2（`clip`）と
#3（`drums`）はその引数の設計、#4 は `write()` の docstring。

### 守るべき互換性

要求元が使っているのは [[TODO-001]] と同じ表の API（`Parser` / `NoteInfo` /
`Player`）のみ。**`transpose()` / `write()` は要求元未使用**なので、
既定値の変更は要求元を壊さない。それでも `clip` は既定 `False`
（= 現行どおり `ValueError`）にして、既存の挙動は維持する。

### ユーザー判断（2026-08-06）

- `drums` の既定は **`transpose()` / `transpose_file()` とも `False`**
  （ch 9 をずらさない）。`transpose()` は 0.1.0 から挙動が変わる
- 回答書は **[[TODO-004]]** に分ける
- **CLI サブコマンド `transpose` を作る**（要求書には無い追加。[[TODO-005]]）

### 設計方針

- **元の `MidiFile` をその場で書き換えて保存する。**
  要求書の案（新しい `MidiFile` を組み立て直す）ではなく、
  `mido.MidiFile()` で読んだオブジェクトの `note_on` / `note_off` の
  `note` だけを書き換えて `save()` する。`type` / `ticks_per_beat` /
  `charset` / メタメッセージ / トラック構成が**自動的にそのまま**残り、
  組み立て直しの取りこぼしが原理的に起きない
- **file-like 対応は `str | os.PathLike[str]` かどうかで分岐する。**
  パスなら `mido.MidiFile(filename=...)` / `save(filename=...)`、
  それ以外は `file=` に渡す（`io.BytesIO` が通る）
- **`mido` の型は公開 API に出さない**（引数も戻り値も `mido` 非依存）
- 範囲外・ch 9 の判定は `transpose()` と共通のヘルパーに置き、
  2 つの関数で意味論が食い違わないようにする

**注意**: 「1 バイトも変わらない」は保証しない（`mido` の再直列化で
running status や delta の符号化が変わりうる）。要求書の受け入れ条件に
挙がっている**メッセージの種類と数・トラック数・`ticks_per_beat`・`type`
の一致**を確認基準とする。

## やったこと

### TODO-003-1. `transpose_file()` の新設（#1・機能追加・最優先）

`midi_writer.py` に追加する。

```python
def transpose_file(
    src: str | os.PathLike[str] | BinaryIO,
    dst: str | os.PathLike[str] | BinaryIO,
    n: int,
    clip: bool = False,
    drums: bool = False,
) -> None:
```

- `note_on` / `note_off` の `note` だけをずらす。他は一切触らない
- `src` / `dst` は パス と file-like（`io.BytesIO` 等）の両方を受ける
- `__init__.py` の `__all__` に追加する
  （`transpose_file` に加えて `DRUM_CHANNEL` も公開した）

### TODO-003-2. `clip` 引数（#2・改善・高）

`transpose()` と `transpose_file()` の**両方**に同じ規則で足した。

- 既定 `clip=False` = 範囲外があれば `ValueError`（現行どおり）
- `clip=True` = 0〜127 に丸める。丸めたときは **WARNING を 1 行**
- 1 個も丸めなければ WARNING は出さない

### TODO-003-3. `drums` 引数（#3・改善・中）

- `drums=False`（既定）で **channel 9 をずらさない**
- `drums=True` で全チャンネルをずらす
- **`transpose()` / `transpose_file()` とも既定 `False`**
- 範囲チェック・クリップの対象からも ch 9 を外す
- docstring に ch 9 の扱いを明記する

判定は `_shift_note()`（モジュール内のヘルパー）に集約し、2 つの関数で
意味論が食い違わないようにした。ch 9 の番号は定数 `DRUM_CHANNEL`。

### TODO-003-4. `write()` の docstring（#4・改善・低）

`NoteInfo` が持たないもの（`program_change` / `control_change` /
`pitch_bend` / メタメッセージ / トラック構成 / テンポ変化）を列挙し、
`transpose_file()` へ誘導する行を足した。

## テスト

当時は `tests/` が無く、一時ディレクトリの検証スクリプトで手動確認した。
**同じ項目は後に [[TODO-006]] で `tests/test_midi_writer.py` に残してある。**

- テンポ変化（2 つの `set_tempo`）・2 トラック・`program_change` /
  `control_change` / `track_name` / `time_signature` を含む MIDI で、
  メッセージの種類と数・トラック数・`ticks_per_beat`・`type` が一致し、
  `note` だけが指定の半音数ずれていること
- `io.BytesIO` で src / dst を往復できること
- `clip=False` / 引数省略で、範囲外が `ValueError`
- `clip=True` で 0〜127 に丸まり、WARNING が 1 行だけ出ること
  （丸めが起きなければ出ないことも確認）
- ch 9 の `note` が `drums=False` で不変、`drums=True` でずれること
- `transpose()`（`NoteInfo` 版）が元のリストを変更しないこと
- lint / 型チェック 3 種がエラー 0・警告 0

完了条件:

- 要求書 #1〜#4 の受け入れ条件をすべて満たす — 完了
  （ただし「1 バイトも変わらない」は保証せず、メッセージ構成の一致で確認）
- 利用側が `import mido` せずに移調を完結できる — 完了
- タグ付け（`0.2.0` 想定）・push はユーザーが行う

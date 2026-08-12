# ytmidilib リファレンスマニュアル

`ytmidilib` を自分のアプリケーションから使うための説明書。

MIDI ライブラリ [mido](https://mido.readthedocs.io/) のラッパーで、
MIDI ファイルを **イベント単位ではなく note 単位** にパージングし、
各 note の開始/終了時刻を曲頭からの絶対秒で持つ形に変換する。
さらに、その結果を鳴らす簡易プレーヤーと、sin波から wav 音源を作る
ユーティリティを持つ。

**音源ファイルやシンセは使わない。** 鳴らす音はすべて実行時に sin波で
合成する。音色を選ぶ機能は無い。

---

## 目次

- [1. インストール](#1-インストール)
- [2. クイックスタート](#2-クイックスタート)
- [3. データ構造](#3-データ構造)
- [4. パージング — `Parser`](#4-パージング--parser)
- [5. 再生 — `Player`](#5-再生--player)
- [6. 移調 — `transpose()` / `transpose_file()`](#6-移調--transpose--transpose_file)
- [7. その他の API](#7-その他の-api)
- [8. ログ](#8-ログ)
- [9. コマンドライン](#9-コマンドライン)
- [10. 制限と注意点](#10-制限と注意点)

---

## 1. インストール

Python 3.13 以上。

```bash
# ライブラリとして、自分のプロジェクトに追加する
uv add git+https://github.com/ytani01/ytmidilib.git

# コマンドとして使う
uv tool install git+https://github.com/ytani01/ytmidilib.git
```

依存は `mido` / `pygame-ce` / `numpy` / `click` / `loguru`。
パージングと移調だけなら音声デバイスは要らない（[10 章](#10-制限と注意点)）。

公開 API は `ytmidilib` の直下からインポートする。

```python
from ytmidilib import (
    Parser, NoteInfo, ParsedMidi, VisualData,   # パージング
    Player,                                     # 再生
    Wav,                                        # 音源生成
    write, transpose, transpose_file,           # 書き出し・移調
    note2freq,                                  # 変換
    FREQ_BASE, NOTE_BASE, NOTE_N,               # 定数
    DEF_TICKS_PER_BEAT, DRUM_CHANNEL,
)
```

バージョンは git タグから決まる（`hatch-vcs`）。

---

## 2. クイックスタート

### 2.1 パージングして再生する

```python
from ytmidilib import Parser, Player

parsed = Parser().parse('song.mid')

with Player() as player:
    player.play(parsed)          # 鳴り終わるまで戻らない
```

`with` を使わない場合は、終わったら `close()` を呼ぶ。

### 2.2 note を取り出して自分で使う

再生せず、解析結果だけを使う例。**音声デバイスは要らない。**

```python
from ytmidilib import Parser

parsed = Parser().parse('song.mid', channel=[0, 1])   # ch 0 と 1 だけ

print('全チャンネル:', sorted(parsed['channel_set']))

for ni in parsed['note_info']:
    print(f'{ni.abs_time:7.3f}s  ch{ni.channel:2d}'
          f'  note={ni.note:3d}  len={ni.length():.3f}s')
```

### 2.3 移調してファイルに書き出す

```python
from ytmidilib import transpose_file

transpose_file('song.mid', 'song_low.mid', -2)        # 2 半音下げる
```

---

## 3. データ構造

### 3.1 `ParsedMidi`

`Parser.parse()` の戻り値。**モジュール間で受け渡す唯一の形式**で、
`Player.play()` はこの形の dict を受け取る。

```python
class ParsedMidi(TypedDict):
    channel_set: set[int]        # 元ファイルに含まれる全チャンネル番号
    note_info: list[NoteInfo]    # velocity > 0 のみ、end_time 設定済み
```

- `channel_set` は **チャンネルを絞り込む前** に集める。
  `parse(channel=[0])` としても、元ファイルにどのチャンネルがあったかが
  分かる
- `note_info` は `abs_time` の昇順（`mido.merge_tracks()` の順）
- `TypedDict` なので実体はただの `dict`。中身を差し替えて
  `Player.play()` に渡してよい

```python
from ytmidilib import transpose

parsed['note_info'] = transpose(parsed['note_info'], 7)
player.play(parsed)
```

### 3.2 `NoteInfo`

1 つの note を表す。

```python
NoteInfo(abs_time: float, channel: int, note: int,
         velocity: int, end_time: float | None = None)
```

| 属性 | 型 | 意味 |
|---|---|---|
| `abs_time` | `float` | 曲頭からの開始時刻 [秒]。`>= 0` |
| `channel` | `int` | MIDI チャンネル。`0` .. `15` |
| `note` | `int` | MIDI ノート番号。`0` .. `127`（60 = 中央ハ） |
| `velocity` | `int` | 強さ。`0` .. `127` |
| `end_time` | `float \| None` | 曲頭からの終了時刻 [秒]。未設定なら `None` |

`abs_time` と `end_time` は、コンストラクタで **小数第 3 位に丸められる**
（`round(x, 3)`）。

メソッド:

- `length() -> float` — 長さ [秒]。`end_time` が `None` なら `0.0`
- `__str__()` — 1 行の文字列。`print(ni)` でそのまま読める

```text
start:0000.500 channel:00 note:060 velocity:100 end:0001.000 length:00.50
```

`Parser.parse()` が返す `note_info` は、**すべて `velocity > 0` で
`end_time` が設定済み**。`None` を気にする必要があるのは、自分で
`NoteInfo` を組み立てたときだけ。

### 3.3 `VisualData`

`Parser.mk_visual()` の戻り値。テキストによる可視化用。

```python
class VisualData(TypedDict):
    note_min: int                  # 使われた最低音のノート番号
    note_max: int                  # 使われた最高音のノート番号
    data: list[dict[str, Any]]     # {'abs_time': float, 'chr': str}
```

`data` の各要素はその時刻の 1 行分で、`chr` は `note_min` から
`note_max` までを 1 文字ずつ並べた文字列。

---

## 4. パージング — `Parser`

```python
Parser(debug: bool = False)
```

`debug` は互換のために残してある引数で、**ログの水準には影響しない**
（[8 章](#8-ログ)）。

### 4.1 `parse()`

```python
parse(midi_file: str | os.PathLike[str],
      channel: list[int] | tuple[int, ...] | None = None) -> ParsedMidi
```

MIDI ファイルを読み、`ParsedMidi` を返す。**これが主役。**

| 引数 | 意味 |
|---|---|
| `midi_file` | ファイル名。`pathlib.Path` も可 |
| `channel` | 残すチャンネルの番号。`None` または空なら全チャンネル |

内部では 3 段階の処理をする。

1. 全トラックを `mido.merge_tracks()` で 1 本に合成し、`set_tempo` を
   追いながら tick を絶対秒に変換する。曲の途中のテンポ変化も反映される。
   `set_tempo` が無いファイルは MIDI 仕様の既定値 120 BPM で計算する
2. `(channel, note)` ごとに開始待ちを積み、対応する `note_off` の時刻を
   開始側の `end_time` へ書き戻す
3. `velocity == 0` のエントリ（消音）を捨てる

**壊れたファイルの扱い:**

- 対応する `note_on` が無い `note_off` は、WARNING を 1 行出して読み飛ばす
- 閉じられなかった `note_on` は、最終イベントの時刻で打ち切る

例外はこのライブラリでは投げず、`mido` のものがそのまま上がる
（存在しないファイルなら `FileNotFoundError`、MIDI として読めなければ
`OSError` / `ValueError` など）。

```python
from pathlib import Path
from ytmidilib import Parser

parser = Parser()
parsed = parser.parse(Path('song.mid'))

print(len(parsed['note_info']), 'notes')
print('末尾:', max(ni.end_time or 0 for ni in parsed['note_info']), 'sec')
```

### 4.2 可視化

`parse -v` が使っているテキスト可視化。再生経路とは独立していて、
音声デバイスは要らない。

```python
mk_visual(data: list[NoteInfo]) -> VisualData
format_visual(v_data: VisualData, channel_set: set[int]) -> str
print_visual(v_data: VisualData, channel_set: set[int]) -> None
```

- `mk_visual()` — `NoteInfo` のリストから `VisualData` を作る
- `format_visual()` — それを 1 つの文字列に整形する（末尾に改行は付かない）
- `print_visual()` — `format_visual()` の結果を `print()` するだけ

チャンネルは文字で表す。`A`-`Z` が開始、`a`-`z` が終了、`|` は鳴り続けて
いる状態、空白は鳴っていない状態。上下の 3 行はノート番号を縦に読む
定規で、左端の数字は時刻 [秒]。

```python
v_data = parser.mk_visual(parsed['note_info'])
text = parser.format_visual(v_data, parsed['channel_set'])
print(text)
```

ch 0 の 60・64 と ch 1 の 67 が鳴る例:

```text
        |00000000|
        |66666666|
        |01234567|
--------+--------+
0000.000|A       |
0000.250||   A   |
0000.500|a   |  B|
0001.000|    a  b|
--------+--------+
        |00000000|
        |66666666|
        |01234567|

CH( 0): A--a
CH( 1): B--b
```

### 4.3 `mk_event_list()`

```python
mk_event_list(data: list[NoteInfo]) -> list[dict[str, Any]]
```

note 単位のデータを、時刻順のイベント列へ戻す。`mk_visual()` が使う。
同時刻のイベントは、同じ note が重ならない範囲でまとめられる。

```python
[{'abs_time': 0.0,
  'event': [{'note': 60, 'channel': 0, 'velocity': 100},
            {'note': 64, 'channel': 0, 'velocity': 100}]}, ...]
```

---

## 5. 再生 — `Player`

```python
Player(rate: int = Player.DEF_RATE, debug: bool = False)
```

パージング済みのデータを sin波で鳴らす。`DEF_RATE` は 22050 Hz。

**音声デバイスが必要。** 無い環境では `pygame.error` になる。

### 5.1 `play()`

```python
play(parsed_midi: ParsedMidi,
     pos_sec: float = 0.0,
     sec_min: float = Player.SEC_MIN,     # 0.02 sec
     sec_max: float = Player.SEC_MAX,     # 1.20 sec
     block: bool = True) -> None
```

| 引数 | 意味 |
|---|---|
| `parsed_midi` | `Parser.parse()` の戻り値 |
| `pos_sec` | 頭出しの位置 [秒]。これより前の note は飛ばす |
| `sec_min` / `sec_max` | 1 音の長さの下限・上限 [秒]。範囲外は丸める |
| `block` | `True` なら鳴り終わるまで戻らない。`False` なら別スレッドで鳴らし、すぐ戻る |

**呼び出しの中で、まず必要な音を全部生成する。** `block` の値によらず、
`play()` から戻った時点で音源は揃っている。音声デバイスが無い場合、
エラーになるのはこの生成の段階。

再生中にもう一度呼ぶと `RuntimeError`。先に `stop()` を呼ぶこと。

再生ループはメインスレッドが `time.sleep()` 相当で刻み、実際の発音は
ワーカースレッドが行う。理想時刻と実時刻の差を次の待ち時間から引くので、
ずれは累積しない。

```python
from ytmidilib import Parser, Player

parsed = Parser().parse('song.mid')

with Player(rate=44100) as player:
    player.play(parsed, pos_sec=30.0)        # 30 秒目から鳴らす
```

### 5.2 止める・状態を見る

```python
is_playing() -> bool     # play(block=False) の再生が続いているか
stop() -> None           # 再生を止める。鳴っている音も止める
close() -> None          # stop() + mixer 終了 + 音源キャッシュ破棄
```

`stop()` の後で `play()` を呼び直せば、また鳴らせる。

```python
import time
from ytmidilib import Parser, Player

parsed = Parser().parse('song.mid')
player = Player()
try:
    player.play(parsed, block=False)         # すぐ戻る
    while player.is_playing():
        time.sleep(0.1)                      # ここで他の仕事もできる
finally:
    player.close()
```

`Player` はコンテキストマネージャなので、`with` を使えば `close()` は
自動で呼ばれる。

### 5.3 音源のキャッシュ

```python
init_mixer() -> None
mk_wav(in_data, sec_min, sec_max) -> dict[tuple[int, float], pygame.mixer.Sound]
snd_key(note_data, sec_min, sec_max) -> tuple[int, float]
```

- `init_mixer()` — pygame の mixer を初期化する。初期化済みなら何もしない。
  `mk_wav()` の先頭で呼ばれるので、普通は自分で呼ばなくてよい
- `mk_wav()` — 必要な音を全部作ってキャッシュする。`play()` が呼ぶ
- `snd_key()` — キャッシュのキー `(ノート番号, 丸めた長さ)` を返す。
  長さを 0.02 秒単位に丸めることで、生成する音源の種類数を抑えている

キャッシュは `close()` で捨てられる。同じ曲を繰り返し鳴らすなら、
`Player` を作り直さず使い回すほうが速い。

---

## 6. 移調 — `transpose()` / `transpose_file()`

用途で使い分ける。

| したいこと | 使うもの |
|---|---|
| 解析結果を移調して、そのまま鳴らす・処理する | `transpose()` |
| MIDI ファイルを移調して、MIDI ファイルとして保存する | `transpose_file()` |

**`parse()` → `transpose()` → `write()` は避けること。**
`NoteInfo` が持たない情報（音色・テンポ変化・トラック構成など）が
すべて落ちる（[10 章](#10-制限と注意点)）。

### 6.1 `transpose()`

```python
transpose(note_info: list[NoteInfo], n: int,
          clip: bool = False, drums: bool = False) -> list[NoteInfo]
```

`NoteInfo` のリストを `n` 半音ずらした **新しいリスト** を返す。
元のリストは変更しない。

| 引数 | 意味 |
|---|---|
| `n` | ずらす半音数。負なら下げる |
| `clip` | `False`（既定）なら、範囲外の音が 1 つでもあれば `ValueError`。`True` なら `0` .. `127` に丸め、丸めたときだけ WARNING を 1 行出す |
| `drums` | `False`（既定）なら channel 9 をずらさない。`True` なら全チャンネルをずらす |

**channel 9（`DRUM_CHANNEL`）は既定でずらさない。** 打楽器チャンネルの
note は音の高さではなく楽器の種類を表すため。ずらさない音は、範囲チェックと
丸めの対象からも外れる。

`clip=False` で範囲外の音があると、**1 音でも失敗させる**（部分的に
移調された結果は返さない）。

```python
from ytmidilib import Parser, Player, transpose

parsed = Parser().parse('song.mid')

try:
    parsed['note_info'] = transpose(parsed['note_info'], 12)
except ValueError as e:
    print(e)                                  # note out of range: ...
    parsed['note_info'] = transpose(parsed['note_info'], 12, clip=True)

with Player() as player:
    player.play(parsed)
```

### 6.2 `transpose_file()`

```python
transpose_file(src, dst, n: int,
               clip: bool = False, drums: bool = False) -> None
```

MIDI ファイルを移調して書き出す。`src` / `dst` は、パス
（`str` / `os.PathLike`）でも、開いたバイナリファイル
（`io.BytesIO` など）でもよい。

**`note_on` / `note_off` の `note` だけを書き換える。** 他のメッセージ・
トラック構成・`ticks_per_beat`・ファイルの type はそのまま。読み込んだ
ファイルをその場で書き換えて保存するため。

ただし `mido` による再直列化を経るので、running status や delta の
符号化までバイト単位で一致することは保証しない。

`clip` / `drums` の意味と既定値は `transpose()` と同じ。`clip=False` で
範囲外の音があれば `ValueError` になり、**`dst` には何も書かない**。

```python
import io
from ytmidilib import transpose_file

# ファイル同士
transpose_file('song.mid', 'song_up.mid', 3)

# メモリ上で
buf = io.BytesIO()
with open('song.mid', 'rb') as f:
    transpose_file(f, buf, -5, clip=True)
data = buf.getvalue()
```

---

## 7. その他の API

### 7.1 `Wav` — sin波の音源

```python
Wav(freq: float, sec: float = Wav.DEF_SEC, rate: int = Wav.DEF_RATE,
    debug: bool = False)
```

コンストラクタの中で音源データを作り、`wav` 属性
（`numpy.ndarray[int16]`、モノラル）に持つ。

| 定数 | 値 | 意味 |
|---|---|---|
| `Wav.DEF_SEC` | `1.0` | 長さ [秒] |
| `Wav.DEF_RATE` | `44100` | サンプリングレート [Hz] |
| `Wav.DEF_VOL` | `0.25` | 音量 |
| `Wav.VOL_MIN` / `VOL_MAX` | `0.0` / `1.0` | 音量の範囲 |

メソッド:

- `mk_wav() -> NDArray[np.int16]` — 音源データを作る。コンストラクタが呼ぶ
- `save(outfile)` — wav 形式で保存する。**音声デバイスは要らない**
- `play(vol=DEF_VOL)` — 鳴らして、鳴り終わるまで待つ。
  範囲外の `vol` は丸めて WARNING を出す

前後にフェードを掛けてクリックノイズを消している。これが無いと
ブツブツ鳴る。

**`play()` は mixer を初期化しない。** 使う前に自分で初期化すること
（`Player` は自前で初期化するので、この手間は要らない）。

```python
import pygame
from ytmidilib import Wav, note2freq

w = Wav(note2freq(60), sec=0.5)
w.save('c4.wav')                              # 保存だけならこれで済む

pygame.mixer.init(frequency=Wav.DEF_RATE, channels=1)
w.play(0.3)
pygame.mixer.quit()
```

### 7.2 `write()` — `NoteInfo` から MIDI ファイル

```python
write(midi_file, note_info: list[NoteInfo],
      ticks_per_beat: int = DEF_TICKS_PER_BEAT,   # 480
      tempo: int = 500000) -> None                # usec/beat, 120 BPM
```

`NoteInfo` のリストを MIDI ファイルへ書き出す。絶対秒を tick に戻し、
`note_on` / `note_off` の並びに展開する。全チャンネルが 1 トラックに入る。

`midi_file` は、パス（`str` / `os.PathLike`）でも、開いたバイナリファイル
（`io.BytesIO` など）でもよい（`transpose_file()` の `dst` と同じ）。
file-like を渡せば、ディスクに何も残さずバイト列が得られる。

`velocity == 0` の要素は捨てる。`end_time` が `None` の音は長さ 0 として
扱う。同時刻では消音を先に置き、同じ note の打ち直しと衝突させない。

**`NoteInfo` が持たないものは書き出されない**（[10 章](#10-制限と注意点)）。
自分で組み立てた note 列を MIDI にするための関数であって、
読んだファイルを書き戻すためのものではない。

```python
import io

from ytmidilib import NoteInfo, write

notes = [
    NoteInfo(0.0, 0, 60, 100, 0.5),
    NoteInfo(0.5, 0, 64, 100, 1.0),
    NoteInfo(1.0, 0, 67, 100, 2.0),
]
write('chord.mid', notes)

# メモリ上で
buf = io.BytesIO()
write(buf, notes)
data = buf.getvalue()
```

### 7.3 `note2freq()` と定数

```python
note2freq(note: int) -> float
```

MIDI ノート番号を周波数 [Hz] に変換する。A4 = note 69 = 440 Hz 基準の
12 平均律。範囲外の値も、そのまま計算した結果を返す（チェックはしない）。

```python
note2freq(69)    # 440.0
note2freq(60)    # 261.6255653005986
```

| 定数 | 値 | 意味 |
|---|---|---|
| `FREQ_BASE` | `440` | 基準の周波数 [Hz] |
| `NOTE_BASE` | `69` | 基準のノート番号（A4） |
| `NOTE_N` | `128` | ノート番号の総数（`0` .. `127`） |
| `DEF_TICKS_PER_BEAT` | `480` | `write()` の既定の分解能 |
| `DRUM_CHANNEL` | `9` | 打楽器チャンネル（0 始まり） |

---

## 8. ログ

`loguru` を使う。既定では何も設定しなくても loguru の既定シンク
（標準エラー、DEBUG 以上）に出る。出力先と水準を決めたい場合は、
`mylog.loggerInit()` を **アプリケーション側で 1 度だけ** 呼ぶ。

```python
import sys
from ytmidilib.mylog import loggerInit, exmsg

loggerInit(debug=False)              # INFO 以上を標準エラーへ
loggerInit(debug=True)               # DEBUG 以上
loggerInit(debug=True, out=sys.stdout)
loggerInit(out='app.log')            # loguru.logger.add() が受ける対象なら可
```

- `loggerInit(debug=False, out=sys.stderr)` — 既存のシンクを全部外し
  （`logger.remove()`）、`out` へのシンクを 1 つ張る
- `exmsg(ex) -> str` — 例外を `ValueError: message` の形の 1 行にする

**`Parser` / `Player` / `Wav` の `debug=` 引数は、ログの水準に影響しない。**
loguru は logger ごとの水準を持てないため、水準を決めるのは
`loggerInit()` だけ。この引数は利用側の互換のために残してある。

ライブラリ側でログを出しているのは、主に次の場面。

| 水準 | 出るところ |
|---|---|
| WARNING | 対応する `note_on` の無い `note_off`、移調で丸めた音、`Wav.play()` の音量の丸め、再生開始の待ちが長すぎる場合 |
| DEBUG | 各処理の入り口、パラメータ、再生の時刻ずれなど |

自分のアプリでシンクを張り替えるなら、`loggerInit()` を呼ばず
`loguru.logger` を直接設定してもよい。

---

## 9. コマンドライン

インストールすると `ytmidilib` コマンドが入る。ソースツリーからは
`uv run ytmidilib ...` で動く。

全サブコマンドに `-d` / `--debug`（ログを DEBUG にする）と
`-h` / `--help` がある。

### `parse` — パージングして表示する

```bash
ytmidilib parse FILE [-c CH]... [-v]
```

| オプション | 意味 |
|---|---|
| `-c` / `--channel CH` | 対象チャンネル。複数指定できる |
| `-v` / `--visual` | テキストで可視化する |

note の一覧と `channel_set` を表示する。再生はしない。

### `play` — 再生する

```bash
ytmidilib play FILE [-s SEC] [-c CH]... [-r RATE] [--min SEC] [--max SEC]
```

| オプション | 既定 | 意味 |
|---|---|---|
| `-s` / `--pos_sec` | `0` | 頭出しの位置 [秒] |
| `-c` / `--channel` | 全部 | 対象チャンネル。複数指定できる |
| `-r` / `--rate` | `22050` | サンプリングレート [Hz] |
| `--sec_min` / `--min` | `0.02` | 1 音の長さの下限 [秒] |
| `--sec_max` / `--max` | `1.2` | 1 音の長さの上限 [秒] |

### `wav` — 単音を作る・鳴らす

```bash
ytmidilib wav FREQ [OUTFILE] [-m] [-v VOL] [-t SEC] [-r RATE] [-n]
```

| オプション | 既定 | 意味 |
|---|---|---|
| `-m` / `--midi_note` | — | `FREQ` を MIDI ノート番号として扱う |
| `-v` / `--vol` | `0.25` | 音量（`0.0` .. `1.0`） |
| `-t` / `-s` / `--sec` | `1.0` | 長さ [秒] |
| `-r` / `--rate` | `44100` | サンプリングレート [Hz] |
| `-n` / `--dont_play` | — | 鳴らさない（保存だけ） |

`OUTFILE` を省くと保存しない。複数書いても、使われるのは 1 つ目だけ。

```bash
ytmidilib wav 440                     # A4 を 1 秒鳴らす
ytmidilib wav 60 c4.wav -m -n         # note 60 を鳴らさずに保存
```

### `transpose` — 移調する

```bash
ytmidilib transpose SRC DST N [-c] [-D]
```

| オプション | 意味 |
|---|---|
| `-c` / `--clip` | 範囲外を `0` .. `127` に丸める（既定はエラー） |
| `-D` / `--drums` | channel 9（打楽器）も移調する |

`N` は半音数で、負の値も書ける（`ytmidilib transpose a.mid b.mid -2`）。
範囲外の音があると、`--clip` を勧めるメッセージを出して終了する。

---

## 10. 制限と注意点

### 音声デバイスが要るところ

| 要る | 要らない |
|---|---|
| `Player.play()` / `Player.mk_wav()` / `Player.init_mixer()`、`Wav.play()`、CLI の `play` | `Parser` の全メソッド、`transpose()` / `transpose_file()` / `write()`、`Wav()` の生成と `save()`、`note2freq()`、CLI の `parse` / `transpose` |

サーバやテストなど、デバイスの無い環境で使うなら右側だけで組み立てる。

### pygame の mixer は共有される

mixer は **モノラル**（`channels=1`）で初期化する。プロセス内で 1 つしか
持てないので、`Player` を複数作ってもレートは最初に初期化した側のものに
なる。`Player.init_mixer()` は初期化済みなら何もしないので、他所が先に
初期化していても二重にはならない。

### `parse()` → `write()` は往復にならない

`NoteInfo` が持たない情報は、`write()` で書き出されない。

- `program_change`（音色）— すべて既定の音色になる
- `control_change`（音量・ペダルなど）
- `pitch_bend`
- メタメッセージ（`track_name` / `time_signature` など）
- トラック構成 — 全チャンネルが 1 トラックに潰れる
- テンポ変化 — 引数 `tempo` の `set_tempo` 1 つに潰れる

**元のファイルを保ったまま移調したいなら `transpose_file()` を使う。**

### 音は sin波だけ

音色は選べない。`velocity` は音量に反映されるが、`program_change` は
無視される。打楽器チャンネル（9）も、note に対応する高さの sin波として
鳴る（移調では既定で除外されるのに、再生では区別しない）。

1 音の長さは `sec_min` .. `sec_max` に丸められるので、長い音は
`sec_max`（既定 1.2 秒）で切れる。伸ばしたければ `sec_max` を大きくする。

---

## 付録. 関連ドキュメント

- [mido — MIDI Objects for Python](https://mido.readthedocs.io/en/latest/)
- `README.md` — 概要と最短の使い方
- `CLAUDE.md` — 内部構造、開発時の決まりごと
- `archives/todo/` — 過去の判断の経緯（**現行仕様ではない**）

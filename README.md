# ytmidilib

Simple MIDI library: Parser, Player, etc.

Python向け MIDIライブラリ ``Mido`` を使って、
より使いやすい形にパージングするライブラリです。

簡単なプレーヤー、wav形式の音源ファイル作成機能などもあります。

特徴
* 全トラックを合成
* channelを選択することが可能
* (イベント単位ではなく) note単位で解析
* note毎に、開始時刻と終了時刻を絶対時間(曲の開始からの秒数)で算出
* noteの情報(`NoteInfo`)は、
  `print()` や `str()` で簡単に内容を確認できる


## TL;DR

Sample program
```python
#!/usr/bin/env python3

import sys
from ytmidilib import *

midi_file = sys.argv[1]
pa = Parser()
pl = Player()

parsed_data = pa.parse(midi_file)

pl.play(parsed_data)
```

## 1. Install

```bash
git clone https://github.com/ytani01/ytmidilib.git
cd ytmidilib
uv tool install .
```

## 2. デモ実行

### 2.1 Execute parser
```bash
ytmidilib parse midi_file
```

### 2.2 Execute player
```bash
ytmidilib play midi_file
```


## 3. for detail

**詳しくは [リファレンスマニュアル](docs/REFERENCE.md) を参照。**
公開API、データ構造、コマンドライン、制限事項をまとめてある。

### 3.1 API

パージングする関数
```bash
uv run python -m pydoc ytmidilib.Parser.parse
```

パージング結果を受けて音楽を再生する関数
```bash
uv run python -m pydoc ytmidilib.Player.play
```

指定されてた周波数の音源データ(wav形式)を作成/再生/保存するクラス
```bash
uv run python -m pydoc ytmidilib.Wav
```

ノート番号を周波数に変換する関数
```bash
uv run python -m pytoc ytmidilib.note2freq
```

### 3.2 parsed data

```
parsed_data = {
  'channel_set': { 元ファイルに含まれている全チャンネル番号 },
  'note_info': [ ノート情報のリスト ]
}
```

パージング結果に含まれているノート情報
(parsed_data['note_info'])
```bash
uv run python -m pydoc ytmidilib.NoteInfo
```


## A. Reference

* [Mido - MIDI Objects for Python](https://mido.readthedocs.io/en/latest/)

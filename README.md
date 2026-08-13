# ytmidilib

Simple MIDI library: Parser, Player, etc.

Python 向け MIDI ライブラリ [mido](https://mido.readthedocs.io/) のラッパー。
MIDI ファイルを、そのまま扱いやすい形に変換します。

簡単なプレーヤーと、wav 形式の音源ファイル作成機能も付いています。


## 特徴

* **note 単位で解析** — イベント単位ではないので、
  note_on と note_off を突き合わせる手間が要らない
* **開始・終了時刻が絶対秒** — 曲頭からの秒数なので、
  tick やテンポ変化を意識せずに扱える（途中のテンポ変化も反映済み）
* **全トラックを 1 本に合成** — トラック構成を気にせず読める。
  チャンネルでの絞り込みも可能
* **そのまま鳴らせる** — 解析結果を渡すだけで再生できる。
  音源ファイルもシンセも要らず、実行時に sin波で合成する
* **読みやすい note 情報** — `print()` や `str()` で内容をそのまま確認できる
* **移調** — 解析結果でも、MIDI ファイルのままでも移調できる


## 使ってみる

```bash
git clone https://github.com/ytani01/ytmidilib.git
cd ytmidilib
uv tool install .

ytmidilib play MIDIファイル
```

自分のプログラムから使う場合:

```python
from ytmidilib import Player, parse

parsed = parse('song.mid')

with Player() as player:
    player.play(parsed)
```


## ドキュメント

* [リファレンスマニュアル](docs/REFERENCE.md) —
  インストール、公開 API、データ構造、コマンドライン、制限事項

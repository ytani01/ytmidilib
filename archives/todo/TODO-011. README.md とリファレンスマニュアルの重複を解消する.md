# TODO-011. README.md とリファレンスマニュアルの重複を解消する

## きっかけ

TODO-008 で `docs/REFERENCE.md` を作ったあと、README.md をそのままに
してあったので、同じことが 2 か所に書かれていた。

| README の箇所 | REFERENCE の対応箇所 |
|---|---|
| TL;DR のサンプル | 2.1 パージングして再生する |
| 1. Install | 1. インストール |
| 2. デモ実行 | 9. コマンドライン |
| 3.1 API（pydoc のコマンド列） | 4 / 5 / 7 章 |
| 3.2 parsed data | 3.1 `ParsedMidi` |
| A. Reference（mido へのリンク） | 付録. 関連ドキュメント |

## やったこと

README.md を「何ができるか」と「どこを読めばよいか」だけにした。
API・データ構造・コマンドラインの詳細は REFERENCE.md に任せる。

削除したもの:

- TL;DR の Python サンプル
- 「2. デモ実行」の parse / play の個別の節
- 「3.1 API」の pydoc コマンド列。
  `uv run python -m pytoc ytmidilib.note2freq` という誤記も含んでいた
- 「3.2 parsed data」の dict の説明
- 「A. Reference」の mido へのリンク

残したもの:

- 「特徴」。箇条書きの各項目に、それで何が嬉しいかを 1 行添えた
- 最短で試せる導線（インストールと `ytmidilib play` を 1 つのブロックに）。
  リンクだけでは、何も動かさないまま REFERENCE を読みに行くことになる
- ライブラリとして使う最小の例。README だけで「短く書ける」ことが分かるように
- REFERENCE.md へのリンク

## テスト

ドキュメントのみの変更で、コードには触れていない。

`docs/REFERENCE.md` の付録に「`README.md` — 概要と最短の使い方」とあり、
書き換え後の内容と合っていることを確認した。

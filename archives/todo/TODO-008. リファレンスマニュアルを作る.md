# TODO-008. `docs/REFERENCE.md`（リファレンスマニュアル）を作る

## きっかけ

`ytmidilib` は `ytstreetorgan` 専用ではなく、他のアプリからも使われうる。
それまで `README.md` は「詳しくは `pydoc` を見よ」と案内するだけで、
公開 API（`__init__.py` の `__all__`）を一覧できる場所が無かった。

利用側が `pydoc` を叩かずに読める形にまとめる。

## 決めたこと

- **分量は「よく使うものを厚く」。** `Parser` / `Player` / `NoteInfo` /
  移調を厚く書き、`Wav` / `write()` / 定数は簡潔に列挙する。
  全 API を同じ密度で網羅する案もあったが、読み物としての使いやすさを
  優先した
- 日本語で書く（既存ドキュメントに合わせる）
- 対象は公開 API と CLI に限る。内部実装（`parse1()` /
  `set_end_time()` / `_play_main()` など）は仕組みの説明が要る範囲だけ
  触れ、詳細は `CLAUDE.md` に任せる

## やったこと

`docs/REFERENCE.md` を新規作成（約 730 行）。構成は次のとおり。

| 章 | 内容 |
|---|---|
| 1–2 | インストール、クイックスタート |
| 3 | データ構造（`ParsedMidi` / `NoteInfo` / `VisualData`） |
| 4–6 | `Parser`、`Player`、`transpose()` / `transpose_file()`（厚い部分） |
| 7 | `Wav`、`write()`、`note2freq()` と定数 |
| 8 | ログ（`loggerInit()`、`debug=` が水準に影響しないこと） |
| 9 | コマンドライン 4 サブコマンド |
| 10 | 制限と注意点 |

他のアプリの作者がつまずきそうな点を、10 章に明示した。

- **音声デバイスが要る API と要らない API の表。** パース・移調・
  wav 保存だけならデバイス不要
- `Wav.play()` は mixer を自分で初期化しない（`Player` はする）
- `parse()` → `write()` は往復にならない。ファイルを保ったまま移調
  するなら `transpose_file()`
- 打楽器チャンネル（9）は移調では既定で除外されるのに、再生では
  区別せず sin波で鳴る
- 音の長さは `sec_max`（既定 1.2 秒）で切れる

`README.md` の「3. for detail」からリンクを張った。

## テスト

コードは変更していないので、テスト・lint は実行していない。
代わりに、書いた内容を実際の出力と突き合わせた。

- `mk_visual()` / `format_visual()` の出力例、`NoteInfo.__str__()` の
  書式、`note2freq()` の値は、実行結果をそのまま載せた
- `write()`、`transpose_file()`（`BytesIO` 経由を含む）、`Wav.save()`
  のコード例は実際に動かして確認した
- CLI のオプションと既定値は `--help` の実出力と突き合わせた

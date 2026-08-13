# TODO

**残っている項目: TODO-025。** これまでに 24 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-026` から。**

---

## TODO-025. ドキュメントを実装に合わせる

`docs/REFERENCE.md` — 実装と食い違っているところ:

- [ ] 5.3 の `mk_wav()` / `snd_key()` の引数（実際は `mk_wav(in_data)` /
      `snd_key(note_data)`。TODO-022 で `sec_min` / `sec_max` を外した）
- [ ] 5.3 の丸めの単位（0.5 秒超は 0.02 単位、0.5 秒以下は 0.01 単位）
- [ ] `init_mixer()` / `quit_mixer()` を載せる。`__all__` にあるのに
      1 章の import 例にも 7 章にも無く、7.1 の例は生の
      `pygame.mixer.init()` のまま。10 章の表も `Player.init_mixer()` だけ
- [ ] 7.4 の `__version__` の例（`'0.2.1'`。現在は `0.5.1`）。
      具体的な番号を書かない形にする
- [ ] 7.1 に `Wav.mk_wav()` の `ValueError`（`sec` が短すぎる場合。
      TODO-017）を足す

`CLAUDE.md` — 実装と食い違っているところ:

- [ ] アーキテクチャの一覧に `midi_writer.py` が無い
- [ ] 「`Player` と `WavApp` がそれぞれ `pygame.mixer.init()` を呼ぶ」
      （実際は両方とも `wav_utils.init_mixer()` 経由）
- [ ] 「各サブコマンドは先頭で `loggerInit(debug)` を呼び」
      （実際は `run_app()` が共通で行う。TODO-018）
- [ ] `midi_utils.py` の説明に `clip_range()` と `DRUM_CHANNEL`
      （TODO-023 で移した）が無い

3 か所に同じ食い違い:

- [ ] 再生ループの待ちは `time.sleep()` ではなく
      `threading.Event.wait()`（TODO-020）。`CLAUDE.md`、
      `docs/REFERENCE.md` 5.1、`midi_player._play_main()` の docstring

決めること:

- [ ] `docs/REFERENCE.md` 8 章の `loggerInit(out='app.log')` は、
      `mylog.loggerInit()` の型注釈 `out: TextIO` と食い違う。
      実行はできるが型チェックは通らない。文書を型に合わせるか、
      型を広げるか（`mylog.py` は `ytstreetorgan` / `tmr` と同一の
      ファイルなので、型を変えるなら他も揃える。TODO-007）

公開していない型別名（`ChannelFilter` / `MidiSource` / `MidiDest`）を
リファレンスに載せるかどうかも、ついでに決める。

モデル・effort: Sonnet / medium。文書だけの直しで、直す箇所は上に
洗い出してある。サブエージェントは編成しない。

---

## 完了済み

1 項目 1 ファイル。`archives/todo/` にある（新しい順）。
**やらないと決めたものの理由もそこにある。** 蒸し返す前に読むこと。

- [**TODO-024.** `click_utils.py` / `mylog.py` に型注釈を付ける](archives/todo/TODO-024.%20click_utils.py%20と%20mylog.py%20に型注釈を付ける.md)
- [**TODO-023.** 定数の置き場所と、`deepcopy` をやめる](archives/todo/TODO-023.%20定数の置き場所と、deepcopy%20をやめる.md)
- [**TODO-022.** `Player` の引数の引き回しを整理する](archives/todo/TODO-022.%20Player%20の引数の引き回しを整理する.md)
- [**TODO-021.** `midi_writer.py` の型を締める](archives/todo/TODO-021.%20midi_writer.py%20の型を締める.md)
- [**TODO-020.** `play -s` で、頭出し位置の秒数だけ無音で待つ](archives/todo/TODO-020.%20play%20-s%20で、頭出し位置の秒数だけ無音で待つ.md)
- [**TODO-019.** docstring の言語とスタイルを揃える](archives/todo/TODO-019.%20docstring%20の言語とスタイルを揃える.md)
- [**TODO-018.** CLI の定型処理と、重複した小さな処理をまとめる](archives/todo/TODO-018.%20CLI%20の定型処理と、重複した小さな処理をまとめる.md)
- [**TODO-017.** `Wav.mk_wav()` が短すぎる音で失敗する](archives/todo/TODO-017.%20Wav.mk_wav%28%29%20が短すぎる音で失敗する.md)
- [**TODO-016.** `Parser` の責務と、解析結果の型を整える](archives/todo/TODO-016.%20Parser%20の責務と、解析結果の型を整える.md)
- [**TODO-015.** ruff の規則を増やす](archives/todo/TODO-015.%20ruff%20の規則を増やす.md)
- [**TODO-014.** `click_utils.py` を導入する](archives/todo/TODO-014.%20click_utils.py%20を導入する.md)
- [**TODO-013.** `write()` を file-like に対応させる（要求書 3 通目）](archives/todo/TODO-013.%20write%28%29%20を%20file-like%20に対応させる（要求書%203%20通目）.md)
- [**TODO-012.** ユーザー全体の `CLAUDE.md` に合わせて記述を整える](archives/todo/TODO-012.%20ユーザー全体の%20CLAUDE.md%20に合わせて記述を整える.md)
- [**TODO-011.** README.md とリファレンスマニュアルの重複を解消する](archives/todo/TODO-011.%20README.md%20とリファレンスマニュアルの重複を解消する.md)
- [**TODO-010.** 要求書・回答書の移動にリンクを追従させる](archives/todo/TODO-010.%20要求書・回答書の移動にリンクを追従させる.md)
- [**TODO-009.** 未使用の依存 `sounddevice` を外す](archives/todo/TODO-009.%20未使用の依存%20sounddevice%20を外す.md)
- [**TODO-008.** リファレンスマニュアルを作る](archives/todo/TODO-008.%20リファレンスマニュアルを作る.md)
- [**TODO-007.** `my_logger.py` を廃止して `mylog.py` へ切り替える](archives/todo/TODO-007.%20my_logger.py%20を廃止して%20mylog.py%20へ切り替える.md)
- [**TODO-006.** テストを整備する（pytest）](archives/todo/TODO-006.%20テストを整備する（pytest）.md)
- [**TODO-005.** CLI サブコマンド `transpose` の追加](archives/todo/TODO-005.%20CLI%20サブコマンド%20transpose%20の追加.md)
- [**TODO-004.** 要求書 2 通目への回答書を作成する](archives/todo/TODO-004.%20要求書%202%20通目への回答書を作成する.md)
- [**TODO-003.** MIDI ファイルの移調（要求書 2 通目）](archives/todo/TODO-003.%20MIDI%20ファイルの移調（要求書%202%20通目）.md)
- [**TODO-002.** 改善要求への回答書を作成する](archives/todo/TODO-002.%20改善要求への回答書を作成する.md)
- [**TODO-001.** `ytstreetorgan` からの改善要求への対応](archives/todo/TODO-001.%20ytstreetorgan%20からの改善要求への対応.md)

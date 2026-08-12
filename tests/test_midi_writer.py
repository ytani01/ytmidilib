#
# (c) 2026 Yoichi Tanibayashi
#
"""
`ytmidilib.midi_writer` のテスト

要求書 2 通目 (`archives/20260806c-ytmidilib-requests-2.md`) の受け入れ条件を、
そのまま自動テストにしたもの。
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2026/08'

import io
from pathlib import Path

import mido
import pytest

from ytmidilib import (
    DEF_TICKS_PER_BEAT, DRUM_CHANNEL, NOTE_N, NoteInfo, Parser,
    transpose, transpose_file, write)
from ytmidilib.midi_parser import DEFAULT_TEMPO

from conftest import CountMsgTypes, LogMessages, MkMidiFile


def _warnings(log_messages: LogMessages) -> list[str]:
    """WARNING のメッセージだけを取り出す"""
    return [msg for level, msg in log_messages if level == 'WARNING']


# --- transpose() ----------------------------------------------------

@pytest.mark.parametrize('n', [1, 2, 12, -1, -2, -12, 0])
def test_transpose_shift(n: int) -> None:
    """全部の音が n 半音ずれる(負なら下がる)"""
    in_data = [
        NoteInfo(0.0, 0, 60, 100, 0.5),
        NoteInfo(0.5, 1, 64, 90, 1.0),
    ]

    out_data = transpose(in_data, n)

    assert [ni.note for ni in out_data] == [60 + n, 64 + n]


def test_transpose_keeps_input() -> None:
    """元のリストは変更しない(新しいリストを返す)"""
    in_data = [NoteInfo(0.0, 0, 60, 100, 0.5)]

    out_data = transpose(in_data, 2)

    assert in_data[0].note == 60
    assert out_data[0] is not in_data[0]


def test_transpose_keeps_other_fields() -> None:
    """note 以外は変えない"""
    in_data = [NoteInfo(1.25, 3, 60, 100, 2.5)]

    out = transpose(in_data, 2)[0]

    assert out.abs_time == 1.25
    assert out.end_time == 2.5
    assert out.channel == 3
    assert out.velocity == 100


def test_transpose_drums_default() -> None:
    """既定 (`drums=False`) では ch 9 をずらさない"""
    in_data = [
        NoteInfo(0.0, 0, 60, 100, 0.5),
        NoteInfo(0.0, DRUM_CHANNEL, 36, 100, 0.5),
    ]

    out_data = transpose(in_data, 2)

    assert [ni.note for ni in out_data] == [62, 36]


def test_transpose_drums_true() -> None:
    """`drums=True` なら ch 9 もずらす"""
    in_data = [NoteInfo(0.0, DRUM_CHANNEL, 36, 100, 0.5)]

    out_data = transpose(in_data, 2, drums=True)

    assert out_data[0].note == 38


def test_transpose_out_of_range() -> None:
    """`clip=False` (既定) なら、範囲外は `ValueError`"""
    in_data = [
        NoteInfo(0.0, 0, 60, 100, 0.5),
        NoteInfo(1.5, 2, 120, 100, 2.0),
    ]

    with pytest.raises(ValueError) as exc_info:
        transpose(in_data, 12)

    msg = str(exc_info.value)
    assert 'note out of range' in msg
    assert '120 + 12 = 132' in msg
    assert 'channel:2' in msg
    # どの音かが分かるように、時刻も入れてある
    assert '1.500' in msg


def test_transpose_out_of_range_low() -> None:
    """下にはみ出す場合も `ValueError`"""
    with pytest.raises(ValueError):
        transpose([NoteInfo(0.0, 0, 5, 100, 0.5)], -6)


def test_transpose_clip(log_messages: LogMessages) -> None:
    """`clip=True` なら 0 .. 127 に丸め、WARNING を 1 行だけ出す"""
    in_data = [
        NoteInfo(0.0, 0, 120, 100, 0.5),
        NoteInfo(0.5, 0, 125, 100, 1.0),
        NoteInfo(1.0, 0, 5, 100, 1.5),
    ]

    out_data = transpose(in_data, 12, clip=True)

    assert [ni.note for ni in out_data] == [NOTE_N - 1, NOTE_N - 1, 17]

    warnings = _warnings(log_messages)
    assert len(warnings) == 1
    assert 'clipped 2 note(s)' in warnings[0]


def test_transpose_clip_low(log_messages: LogMessages) -> None:
    """下にはみ出す場合は 0 に丸める"""
    out_data = transpose([NoteInfo(0.0, 0, 5, 100, 0.5)], -6, clip=True)

    assert out_data[0].note == 0
    assert len(_warnings(log_messages)) == 1


def test_transpose_clip_no_warning(log_messages: LogMessages) -> None:
    """1 つも丸めなければ WARNING は出さない"""
    transpose([NoteInfo(0.0, 0, 60, 100, 0.5)], 2, clip=True)

    assert _warnings(log_messages) == []


def test_transpose_drums_skip_range_check() -> None:
    """ずらさない ch 9 は、範囲チェックの対象からも外れる"""
    in_data = [NoteInfo(0.0, DRUM_CHANNEL, NOTE_N - 1, 100, 0.5)]

    # drums=False なので、はみ出しようが無い
    out_data = transpose(in_data, 12)
    assert out_data[0].note == NOTE_N - 1

    # drums=True にすると、こんどは範囲外になる
    with pytest.raises(ValueError):
        transpose(in_data, 12, drums=True)


# --- transpose_file() -----------------------------------------------

def test_transpose_file_keeps_everything(
        rich_midi_file: Path, tmp_path: Path,
        count_msg_types: CountMsgTypes) -> None:
    """`note` 以外は変わらない

    要求書 #1 の受け入れ条件そのもの。メッセージの種類と数・トラック数・
    `ticks_per_beat`・`type` が一致し、`note` だけがずれていること。
    (バイト単位の一致は `mido` の再直列化があるので保証しない)
    """
    dst = tmp_path / 'out.mid'

    transpose_file(rich_midi_file, dst, 2)

    src_obj = mido.MidiFile(rich_midi_file)
    dst_obj = mido.MidiFile(dst)

    assert count_msg_types(dst_obj) == count_msg_types(src_obj)
    assert len(dst_obj.tracks) == len(src_obj.tracks)
    assert dst_obj.ticks_per_beat == src_obj.ticks_per_beat
    assert dst_obj.type == src_obj.type

    # 音色・音量・メタ・トラック構成が残っている
    msg_types = count_msg_types(dst_obj)
    assert msg_types['program_change'] == 1
    assert msg_types['control_change'] == 1
    assert msg_types['track_name'] == 2
    assert msg_types['time_signature'] == 1
    assert msg_types['set_tempo'] == 2

    # 1 メッセージずつ突き合わせる。note 以外は delta time も含めて同一
    for src_track, dst_track in zip(src_obj.tracks, dst_obj.tracks,
                                    strict=True):
        for src_msg, dst_msg in zip(src_track, dst_track, strict=True):
            if (src_msg.type in ('note_on', 'note_off')
                    and src_msg.channel != DRUM_CHANNEL):
                assert dst_msg.note == src_msg.note + 2
                assert dst_msg.copy(note=src_msg.note) == src_msg
            else:
                assert dst_msg == src_msg


def test_transpose_file_bytesio(rich_midi_file: Path) -> None:
    """src / dst に file-like (`io.BytesIO`) を渡せる"""
    src = io.BytesIO(rich_midi_file.read_bytes())
    dst = io.BytesIO()

    transpose_file(src, dst, 2)

    dst.seek(0)
    dst_obj = mido.MidiFile(file=dst)

    notes = [msg.note for track in dst_obj.tracks for msg in track
             if msg.type == 'note_on' and msg.channel == 0]
    assert notes == [62, 66]


def test_transpose_file_str_path(rich_midi_file: Path,
                                 tmp_path: Path) -> None:
    """ファイル名は `str` でも `os.PathLike` でも受ける"""
    dst = tmp_path / 'out.mid'

    transpose_file(str(rich_midi_file), str(dst), 1)

    assert dst.exists()


def test_transpose_file_drums(rich_midi_file: Path, tmp_path: Path) -> None:
    """ch 9 の扱いは `transpose()` と同じ"""
    dst_keep = tmp_path / 'keep.mid'
    dst_shift = tmp_path / 'shift.mid'

    transpose_file(rich_midi_file, dst_keep, 2)
    transpose_file(rich_midi_file, dst_shift, 2, drums=True)

    def drum_notes(midi_file: Path) -> list[int]:
        midi_obj = mido.MidiFile(midi_file)
        return [msg.note for track in midi_obj.tracks for msg in track
                if msg.type == 'note_on' and msg.channel == DRUM_CHANNEL]

    assert drum_notes(dst_keep) == [36]
    assert drum_notes(dst_shift) == [38]


def test_transpose_file_out_of_range(rich_midi_file: Path,
                                     tmp_path: Path) -> None:
    """範囲外は `ValueError`。dst には何も書かない"""
    dst = tmp_path / 'out.mid'

    with pytest.raises(ValueError) as exc_info:
        transpose_file(rich_midi_file, dst, 100)

    assert 'note out of range' in str(exc_info.value)
    assert not dst.exists()


def test_transpose_file_clip(rich_midi_file: Path, tmp_path: Path,
                             log_messages: LogMessages) -> None:
    """`clip=True` で 0 .. 127 に丸め、WARNING を 1 行だけ出す"""
    dst = tmp_path / 'out.mid'

    transpose_file(rich_midi_file, dst, 100, clip=True)

    dst_obj = mido.MidiFile(dst)
    notes = [msg.note for track in dst_obj.tracks for msg in track
             if msg.type in ('note_on', 'note_off') and msg.channel == 0]
    assert notes == [NOTE_N - 1] * 4

    warnings = _warnings(log_messages)
    assert len(warnings) == 1
    assert 'clipped 4 note(s)' in warnings[0]


def test_transpose_file_clip_skips_drums(rich_midi_file: Path,
                                         tmp_path: Path) -> None:
    """`drums=False` なら、ch 9 は clip の対象にもならない"""
    dst = tmp_path / 'out.mid'

    transpose_file(rich_midi_file, dst, 100, clip=True)

    dst_obj = mido.MidiFile(dst)
    drums = [msg.note for track in dst_obj.tracks for msg in track
             if msg.type == 'note_on' and msg.channel == DRUM_CHANNEL]
    assert drums == [36]


# --- write() --------------------------------------------------------

def test_write_roundtrip(tmp_path: Path) -> None:
    """`write()` -> `parse()` で、時刻・note・velocity が保たれる"""
    midi_file = tmp_path / 'out.mid'
    in_data = [
        NoteInfo(0.0, 0, 60, 100, 0.5),
        NoteInfo(0.5, 1, 64, 90, 1.5),
        NoteInfo(1.0, 9, 36, 80, 1.25),
    ]

    write(midi_file, in_data)

    parsed = Parser().parse(midi_file)

    assert [(ni.channel, ni.note, ni.abs_time, ni.end_time)
            for ni in parsed['note_info']] == [
        (0, 60, 0.0, 0.5),
        (1, 64, 0.5, 1.5),
        (9, 36, 1.0, 1.25),
    ]
    assert [ni.velocity for ni in parsed['note_info']] == [100, 90, 80]
    assert parsed['channel_set'] == {0, 1, 9}


@pytest.mark.parametrize('reverse', [False, True])
def test_write_note_off_first(tmp_path: Path, reverse: bool) -> None:
    """同時刻では、消音を先に置く(同じ note の再打鍵と衝突させない)

    **入力の並び順に関わらず**そうなること。並び順が時刻順なら、
    たまたま消音が先に来るので、逆順でも確かめる。
    """
    midi_file = tmp_path / 'out.mid'
    in_data = [
        NoteInfo(0.0, 0, 60, 100, 0.5),
        NoteInfo(0.5, 0, 60, 100, 1.0),
    ]

    if reverse:
        in_data.reverse()

    write(midi_file, in_data)

    midi_obj = mido.MidiFile(midi_file)
    types = [msg.type for track in midi_obj.tracks for msg in track
             if msg.type in ('note_on', 'note_off')]

    assert types == ['note_on', 'note_off', 'note_on', 'note_off']

    # 潰れずに 2 音として読み直せる
    parsed = Parser().parse(midi_file)
    assert [(ni.abs_time, ni.end_time) for ni in parsed['note_info']] == [
        (0.0, 0.5), (0.5, 1.0)]


def test_write_end_time_none(tmp_path: Path) -> None:
    """`end_time` が未設定の音は、長さ 0 として書く"""
    midi_file = tmp_path / 'out.mid'

    write(midi_file, [NoteInfo(0.5, 0, 60, 100)])

    parsed = Parser().parse(midi_file)
    ni = parsed['note_info'][0]

    assert ni.abs_time == 0.5
    assert ni.length() == 0.0


def test_write_skip_velocity0(tmp_path: Path) -> None:
    """velocity 0 のエントリは書き出さない"""
    midi_file = tmp_path / 'out.mid'

    write(midi_file, [NoteInfo(0.0, 0, 60, 0, 1.0)])

    midi_obj = mido.MidiFile(midi_file)
    notes = [msg for track in midi_obj.tracks for msg in track
             if msg.type in ('note_on', 'note_off')]

    assert notes == []


def test_write_ticks_per_beat_and_tempo(tmp_path: Path) -> None:
    """`ticks_per_beat` / `tempo` の指定が出力に反映される"""
    midi_file = tmp_path / 'out.mid'
    tempo = DEFAULT_TEMPO // 2

    write(midi_file, [NoteInfo(0.0, 0, 60, 100, 0.5)],
          ticks_per_beat=960, tempo=tempo)

    midi_obj = mido.MidiFile(midi_file)

    assert midi_obj.ticks_per_beat == 960

    set_tempo = [msg for track in midi_obj.tracks for msg in track
                 if msg.type == 'set_tempo']
    assert len(set_tempo) == 1
    assert set_tempo[0].tempo == tempo

    # tick に戻した長さも、指定した分解能とテンポで計算されている
    assert round(mido.second2tick(0.5, 960, tempo)) == 1920

    # 読み直せば元の秒に戻る
    parsed = Parser().parse(midi_file)
    assert parsed['note_info'][0].length() == pytest.approx(0.5)


def test_write_default_ticks_per_beat(tmp_path: Path) -> None:
    """既定の分解能は `DEF_TICKS_PER_BEAT`"""
    midi_file = tmp_path / 'out.mid'

    write(midi_file, [NoteInfo(0.0, 0, 60, 100, 0.5)])

    assert mido.MidiFile(midi_file).ticks_per_beat == DEF_TICKS_PER_BEAT


def test_write_bytesio(tmp_path: Path) -> None:
    """`midi_file` に file-like を渡せる。パスに書いたものと一致する"""
    in_data = [
        NoteInfo(0.0, 0, 60, 100, 0.5),
        NoteInfo(0.5, 1, 64, 90, 1.5),
    ]
    midi_file = tmp_path / 'out.mid'
    buf = io.BytesIO()

    write(midi_file, in_data)
    write(buf, in_data)

    buf.seek(0)
    buf_obj = mido.MidiFile(file=buf)
    path_obj = mido.MidiFile(midi_file)

    assert len(buf_obj.tracks) == len(path_obj.tracks)
    assert buf_obj.ticks_per_beat == path_obj.ticks_per_beat
    assert [list(track) for track in buf_obj.tracks] == [
        list(track) for track in path_obj.tracks]


def test_write_str_path(tmp_path: Path) -> None:
    """ファイル名は `str` でも `os.PathLike` でも受ける"""
    midi_file = tmp_path / 'out.mid'

    write(str(midi_file), [NoteInfo(0.0, 0, 60, 100, 0.5)])

    assert midi_file.exists()


def test_write_transposed(tmp_path: Path, mk_midi_file: MkMidiFile) -> None:
    """`parse()` -> `transpose()` -> `write()` が通る(従来の経路)"""
    track = [
        mido.Message('note_on', channel=0, note=60, velocity=100, time=0),
        mido.Message('note_off', channel=0, note=60, velocity=0, time=480),
    ]
    src = mk_midi_file([track])
    dst = tmp_path / 'out.mid'

    parser = Parser()
    parsed = parser.parse(src)
    write(dst, transpose(parsed['note_info'], 2))

    assert [ni.note for ni in parser.parse(dst)['note_info']] == [62]

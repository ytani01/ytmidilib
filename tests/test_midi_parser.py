#
# (c) 2026 Yoichi Tanibayashi
#
"""
`ytmidilib.midi_parser` のテスト
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2026/08'

import logging
from pathlib import Path

import mido
import pytest

from ytmidilib import DRUM_CHANNEL, NoteInfo, Parser
from ytmidilib.midi_parser import DEFAULT_TEMPO

from conftest import MkMidiFile

TPB = 480
"""テストで使う分解能 [tick/beat]"""

BEAT_SEC = 0.5
"""DEFAULT_TEMPO (120 BPM) での 1 beat = 480 tick の長さ [sec]"""


# --- NoteInfo -------------------------------------------------------

def test_noteinfo_round() -> None:
    """時刻は小数第 3 位に丸められる"""
    ni = NoteInfo(1.23456, 0, 60, 100, 2.34567)

    assert ni.abs_time == 1.235
    assert ni.end_time == 2.346


def test_noteinfo_length() -> None:
    """長さは end_time - abs_time。未設定なら 0.0"""
    assert NoteInfo(1.0, 0, 60, 100, 2.5).length() == pytest.approx(1.5)
    assert NoteInfo(1.0, 0, 60, 100).length() == 0.0


def test_noteinfo_str() -> None:
    """`__str__()` は end_time の有無で形が変わる"""
    str_open = str(NoteInfo(1.0, 3, 60, 100))
    str_closed = str(NoteInfo(1.0, 3, 60, 100, 2.5))

    assert 'start:0001.000' in str_open
    assert 'channel:03' in str_open
    assert 'note:060' in str_open
    assert 'velocity:100' in str_open
    assert 'end:' not in str_open

    assert 'end:0002.500' in str_closed
    assert 'length:01.50' in str_closed


# --- Parser.parse1() ------------------------------------------------

def test_parse1_tick2sec(mk_midi_file: MkMidiFile) -> None:
    """tick が曲頭からの絶対秒になる"""
    track = [
        mido.Message('note_on', channel=0, note=60, velocity=100, time=0),
        mido.Message('note_off', channel=0, note=60, velocity=0, time=TPB),
    ]
    midi_file = mk_midi_file([track], ticks_per_beat=TPB)

    _, data = Parser().parse1(mido.MidiFile(midi_file))

    assert [d.abs_time for d in data] == [0.0, BEAT_SEC]


def test_parse1_without_set_tempo(mk_midi_file: MkMidiFile) -> None:
    """`set_tempo` が無いファイルも 120 BPM として正しい秒になる"""
    track = [
        mido.Message('note_on', channel=0, note=60, velocity=100, time=0),
        mido.Message('note_off', channel=0, note=60, velocity=0,
                     time=TPB * 2),
    ]
    midi_file = mk_midi_file([track], ticks_per_beat=TPB)

    midi_obj = mido.MidiFile(midi_file)
    assert not any(msg.type == 'set_tempo'
                   for track in midi_obj.tracks for msg in track)

    _, data = Parser().parse1(midi_obj)

    assert data[-1].abs_time == pytest.approx(BEAT_SEC * 2)


def test_parse1_tempo_change(rich_midi_file: Path) -> None:
    """テンポ変化に追随する

    `rich_midi_file` は 960 tick の時点で 500000 -> 250000 に変わる。
    それ以降は同じ tick 数でも半分の秒数になる。
    """
    _, data = Parser().parse1(mido.MidiFile(rich_midi_file))

    ent = {(d.channel, d.note, d.velocity > 0): d.abs_time for d in data}

    assert ent[(0, 60, True)] == pytest.approx(0.0)
    assert ent[(0, 60, False)] == pytest.approx(0.5)
    assert ent[(0, 64, True)] == pytest.approx(0.5)
    assert ent[(0, 64, False)] == pytest.approx(1.0)
    # ここから倍のテンポ。240 tick が 0.25 秒ではなく 0.125 秒
    assert ent[(DRUM_CHANNEL, 36, False)] == pytest.approx(1.125)


def test_parse1_merge_tracks(mk_midi_file: MkMidiFile) -> None:
    """全トラックが 1 本に合成される"""
    track1 = [
        mido.Message('note_on', channel=0, note=60, velocity=100, time=0),
        mido.Message('note_off', channel=0, note=60, velocity=0, time=TPB),
    ]
    track2 = [
        mido.Message('note_on', channel=1, note=64, velocity=80, time=TPB),
        mido.Message('note_off', channel=1, note=64, velocity=0, time=TPB),
    ]
    midi_file = mk_midi_file([track1, track2], ticks_per_beat=TPB)

    _, data = Parser().parse1(mido.MidiFile(midi_file))

    assert [(d.channel, d.note, d.abs_time) for d in data] == [
        (0, 60, 0.0),
        (0, 60, BEAT_SEC),
        (1, 64, BEAT_SEC),
        (1, 64, BEAT_SEC * 2),
    ]


def test_parse1_channel_set_before_filter(rich_midi_file: Path) -> None:
    """`channel_set` はチャンネルを絞り込む前に集める"""
    channel_set, data = Parser().parse1(
        mido.MidiFile(rich_midi_file), channel=[0])

    # 絞り込んだ結果には ch 9 が無い
    assert {d.channel for d in data} == {0}
    # それでも、元ファイルに ch 9 があったことは分かる
    assert channel_set == {0, DRUM_CHANNEL}


def test_parse1_note_on_velocity0_is_note_off(
        mk_midi_file: MkMidiFile) -> None:
    """velocity 0 の `note_on` は消音として扱う"""
    track = [
        mido.Message('note_on', channel=0, note=60, velocity=100, time=0),
        mido.Message('note_on', channel=0, note=60, velocity=0, time=TPB),
    ]
    midi_file = mk_midi_file([track], ticks_per_beat=TPB)

    _, data = Parser().parse1(mido.MidiFile(midi_file))

    assert [d.velocity for d in data] == [100, 0]


# --- Parser.set_end_time() ------------------------------------------

def test_set_end_time_simple() -> None:
    """対応する消音の時刻が `end_time` に入る"""
    in_data = [
        NoteInfo(0.0, 0, 60, 100),
        NoteInfo(1.0, 0, 60, 0),
    ]

    out_data = Parser().set_end_time(in_data)

    assert out_data[0].end_time == 1.0
    assert out_data[0].length() == pytest.approx(1.0)


def test_set_end_time_fifo() -> None:
    """同じ (channel, note) が重なったら、先に始まった音から閉じる"""
    in_data = [
        NoteInfo(0.0, 0, 60, 100),
        NoteInfo(0.25, 0, 60, 100),
        NoteInfo(0.5, 0, 60, 0),
        NoteInfo(0.75, 0, 60, 0),
    ]

    out_data = Parser().set_end_time(in_data)

    assert out_data[0].end_time == 0.5
    assert out_data[1].end_time == 0.75


def test_set_end_time_orphan_note_off(
        caplog: pytest.LogCaptureFixture) -> None:
    """対応する `note_on` が無い消音は、警告して読み飛ばす"""
    in_data = [
        NoteInfo(0.5, 3, 60, 0),
        NoteInfo(1.0, 0, 64, 100),
        NoteInfo(2.0, 0, 64, 0),
    ]

    with caplog.at_level(logging.WARNING):
        out_data = Parser().set_end_time(in_data)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert 'no note_on' in warnings[0].getMessage()
    assert 'channel:03' in warnings[0].getMessage()
    assert 'note:060' in warnings[0].getMessage()

    # 読み飛ばしても、他の音は正しく閉じられる
    assert out_data[1].end_time == 2.0


def test_set_end_time_unclosed_note() -> None:
    """閉じられなかった音は、最終イベントの時刻で打ち切る"""
    in_data = [
        NoteInfo(0.0, 0, 60, 100),
        NoteInfo(0.5, 0, 64, 100),
        NoteInfo(1.0, 0, 64, 0),
    ]

    out_data = Parser().set_end_time(in_data)

    assert out_data[0].end_time == 1.0


def test_set_end_time_keeps_input() -> None:
    """引数のリストは変更しない"""
    in_data = [
        NoteInfo(0.0, 0, 60, 100),
        NoteInfo(1.0, 0, 60, 0),
    ]

    Parser().set_end_time(in_data)

    assert in_data[0].end_time is None


# --- Parser.parse() -------------------------------------------------

def test_parse(rich_midi_file: Path) -> None:
    """消音のエントリは落とし、鳴る音だけを返す"""
    parsed = Parser().parse(rich_midi_file)

    assert parsed['channel_set'] == {0, DRUM_CHANNEL}

    note_info = parsed['note_info']
    assert all(ni.velocity > 0 for ni in note_info)
    assert [(ni.channel, ni.note, ni.abs_time, ni.end_time)
            for ni in note_info] == [
        (0, 60, 0.0, 0.5),
        (0, 64, 0.5, 1.0),
        (DRUM_CHANNEL, 36, 1.0, 1.125),
    ]


def test_parse_channel_filter(rich_midi_file: Path) -> None:
    """チャンネルを絞り込んでも `channel_set` は元のまま"""
    parsed = Parser().parse(rich_midi_file, channel=[DRUM_CHANNEL])

    assert parsed['channel_set'] == {0, DRUM_CHANNEL}
    assert [ni.channel for ni in parsed['note_info']] == [DRUM_CHANNEL]


def test_parse_accepts_pathlike(rich_midi_file: Path) -> None:
    """ファイル名は `str` でも `os.PathLike` でも受ける"""
    parser = Parser()

    by_path = parser.parse(rich_midi_file)
    by_str = parser.parse(str(rich_midi_file))

    assert len(by_path['note_info']) == len(by_str['note_info'])


# --- Parser.mk_event_list() -----------------------------------------

def test_mk_event_list_merge_same_time() -> None:
    """同時刻の別々の note は 1 つのイベントにまとまる"""
    data = [
        NoteInfo(0.0, 0, 60, 100, 1.0),
        NoteInfo(0.0, 1, 64, 100, 1.0),
    ]

    ev = Parser().mk_event_list(data)

    assert len(ev) == 2
    assert {e1['note'] for e1 in ev[0]['event']} == {60, 64}
    assert ev[0]['abs_time'] == 0.0
    assert ev[1]['abs_time'] == 1.0


def test_mk_event_list_dont_merge_same_note() -> None:
    """同時刻でも、同じ note はまとめない(消音と再打鍵が潰れないように)"""
    data = [
        NoteInfo(0.0, 0, 60, 100, 0.5),
        NoteInfo(0.5, 0, 60, 100, 1.0),
    ]

    ev = Parser().mk_event_list(data)

    at_05 = [e for e in ev if e['abs_time'] == 0.5]
    assert len(at_05) == 2
    assert sorted(e['event'][0]['velocity'] for e in at_05) == [0, 100]


def test_mk_event_list_skip_velocity0() -> None:
    """velocity 0 のエントリは無視する"""
    data = [NoteInfo(0.0, 0, 60, 0, 1.0)]

    assert Parser().mk_event_list(data) == []


# --- Parser.mk_visual() / format_visual() ---------------------------

def test_mk_visual_note_range() -> None:
    """鳴った音の範囲だけを切り出す"""
    data = [
        NoteInfo(0.0, 0, 60, 100, 1.0),
        NoteInfo(0.0, 1, 64, 100, 1.0),
    ]

    v_data = Parser().mk_visual(data)

    assert v_data['note_min'] == 60
    assert v_data['note_max'] == 64
    assert all(len(v['chr']) == 5 for v in v_data['data'])


def test_mk_visual_start_stop_chr() -> None:
    """開始は `A-Z`、終了は `a-z`。文字はチャンネル番号で決まる"""
    data = [
        NoteInfo(0.0, 0, 60, 100, 1.0),
        NoteInfo(0.0, 1, 64, 100, 1.0),
    ]

    v_data = Parser().mk_visual(data)

    assert v_data['data'][0]['chr'] == 'A   B'
    assert v_data['data'][1]['chr'] == 'a   b'


def test_mk_visual_overlapped_note() -> None:
    """二重に鳴っている音は、片方が終わっても継続中 (`|`) のまま

    note 60 が 0.0 .. 0.5 と 0.25 .. 0.75 で重なる。0.5 で 1 つ終わるが、
    まだもう 1 つ鳴っているので、次の行では消えていない。
    """
    data = [
        NoteInfo(0.0, 0, 60, 100, 0.5),
        NoteInfo(0.25, 0, 60, 100, 0.75),
        NoteInfo(0.6, 0, 72, 100, 0.9),
    ]

    v_data = Parser().mk_visual(data)
    lines = {v['abs_time']: v['chr'] for v in v_data['data']}

    assert v_data['note_min'] == 60
    assert v_data['note_max'] == 72

    # 0.5 で 1 つ目が終わる (この行には終了の 'a' が出る)
    assert lines[0.5][0] == 'a'
    # 次の行では、まだ 2 つ目が鳴っているので継続中
    assert lines[0.6][0] == '|'
    # 2 つ目も終わったあとは消えている
    assert lines[0.9][0] == ' '


def test_format_visual() -> None:
    """枠線・ルーラー・凡例の体裁"""
    data = [
        NoteInfo(0.0, 0, 60, 100, 1.0),
        NoteInfo(0.0, 1, 64, 100, 1.0),
    ]

    parser = Parser()
    text = parser.format_visual(parser.mk_visual(data), {0, 1})
    lines = text.split('\n')

    # ノート番号を縦 3 行で表す (060 .. 064)
    assert lines[0] == f'{" ":8}|00000|'
    assert lines[1] == f'{" ":8}|66666|'
    assert lines[2] == f'{" ":8}|01234|'

    border = '--------+-----+'
    assert lines[3] == border
    assert lines[4] == '0000.000|A   B|'
    assert lines[5] == '0001.000|a   b|'
    assert lines[6] == border

    # 末尾はチャンネルの凡例
    assert text.endswith('CH( 0): A--a\nCH( 1): B--b')


def test_print_visual(capsys: pytest.CaptureFixture[str]) -> None:
    """`print_visual()` は `format_visual()` を出力するだけ"""
    data = [NoteInfo(0.0, 0, 60, 100, 1.0)]

    parser = Parser()
    v_data = parser.mk_visual(data)
    parser.print_visual(v_data, {0})

    captured = capsys.readouterr()
    assert captured.out == parser.format_visual(v_data, {0}) + '\n'


def test_default_tempo_is_120bpm() -> None:
    """既定テンポは 120 BPM 相当"""
    assert DEFAULT_TEMPO == mido.bpm2tempo(120)

#
# (c) 2026 Yoichi Tanibayashi
#
"""
`ytmidilib.midi_visual` のテスト
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2026/08'

import pytest

from ytmidilib import (
    NoteInfo,
    Parser,
    format_visual,
    mk_visual,
    print_visual,
)


def test_mk_visual_note_range() -> None:
    """鳴った音の範囲だけを切り出す"""
    data = [
        NoteInfo(0.0, 0, 60, 100, 1.0),
        NoteInfo(0.0, 1, 64, 100, 1.0),
    ]

    v_data = mk_visual(data)

    assert v_data['note_min'] == 60
    assert v_data['note_max'] == 64
    assert all(len(v['chr']) == 5 for v in v_data['data'])


def test_mk_visual_start_stop_chr() -> None:
    """開始は `A-Z`、終了は `a-z`。文字はチャンネル番号で決まる"""
    data = [
        NoteInfo(0.0, 0, 60, 100, 1.0),
        NoteInfo(0.0, 1, 64, 100, 1.0),
    ]

    v_data = mk_visual(data)

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

    v_data = mk_visual(data)
    lines = {v['abs_time']: v['chr'] for v in v_data['data']}

    assert v_data['note_min'] == 60
    assert v_data['note_max'] == 72

    # 0.5 で 1 つ目が終わる (この行には終了の 'a' が出る)
    assert lines[0.5][0] == 'a'
    # 次の行では、まだ 2 つ目が鳴っているので継続中
    assert lines[0.6][0] == '|'
    # 2 つ目も終わったあとは消えている
    assert lines[0.9][0] == ' '


def test_mk_visual_empty() -> None:
    """鳴る音が無ければ、行も無い"""
    v_data = mk_visual([])

    assert v_data['data'] == []


def test_format_visual() -> None:
    """枠線・ルーラー・凡例の体裁"""
    data = [
        NoteInfo(0.0, 0, 60, 100, 1.0),
        NoteInfo(0.0, 1, 64, 100, 1.0),
    ]

    text = format_visual(mk_visual(data), {0, 1})
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

    v_data = mk_visual(data)
    print_visual(v_data, {0})

    captured = capsys.readouterr()
    assert captured.out == format_visual(v_data, {0}) + '\n'


def test_parser_delegates(capsys: pytest.CaptureFixture[str]) -> None:
    """`Parser` の可視化メソッドは、このモジュールの関数を呼ぶだけ"""
    data = [NoteInfo(0.0, 0, 60, 100, 1.0)]
    parser = Parser()

    v_data = parser.mk_visual(data)
    assert v_data == mk_visual(data)

    assert parser.format_visual(v_data, {0}) == format_visual(v_data, {0})

    parser.print_visual(v_data, {0})
    assert capsys.readouterr().out == format_visual(v_data, {0}) + '\n'

#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
MIDI visualizer

解析結果 (`NoteInfo` のリスト) をテキストで可視化する (`parse -v`)。
再生経路とは独立しているので、音声デバイスは要らない。

`midi_parser.py` から分けたもの (TODO-016)。`Parser` の同名メソッドは、
ここへの委譲として残してある。
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2021/01'

from typing import TypedDict

from loguru import logger

from .midi_parser import NoteInfo, mk_event_list
from .midi_utils import NOTE_N

V_CHR_ON = '|'
"""鳴り続けている状態を表す文字"""

V_CHR_OFF = ' '
"""鳴っていない状態を表す文字"""

V_CHR_START = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
"""鳴り始めを表す文字。チャンネル番号で選ぶ"""

V_CHR_STOP = 'abcdefghijklmnopqrstuvwxyz'
"""鳴り終わりを表す文字。チャンネル番号で選ぶ"""


class VisualLine(TypedDict):
    """可視化した1行。`chr` は note_min .. note_max を1文字ずつ並べたもの"""
    abs_time: float
    chr: str


class VisualData(TypedDict):
    """`mk_visual()` の戻り値"""
    note_min: int
    note_max: int
    data: list[VisualLine]


def mk_visual(data: list[NoteInfo]) -> VisualData:
    """テキストによる可視化データを作る

    Parameters
    ----------
    data: list of NoteInfo
    """
    ev = mk_event_list(data)

    note_min = NOTE_N - 1
    note_max = 0

    # 行ごとの (時刻, note ごとの文字)。文字列にまとめるのは、
    # note の範囲が確定する最後
    rows: list[tuple[float, list[str]]] = []
    prev_chr_list = [V_CHR_OFF] * NOTE_N
    on_count = [0] * NOTE_N

    for e in ev:
        cur_chr_list = list(prev_chr_list)
        rows.append((e['abs_time'], cur_chr_list))

        for e1 in e['event']:
            note = e1['note']

            note_min = min(note, note_min)
            note_max = max(note, note_max)

            if e1['velocity'] > 0:
                ch1 = V_CHR_START[e1['channel']]
                on_count[note] += 1
                ch2 = V_CHR_ON
            else:
                ch1 = V_CHR_STOP[e1['channel']]
                on_count[note] -= 1
                ch2 = V_CHR_ON if on_count[note] > 0 else V_CHR_OFF

            cur_chr_list[note] = ch1
            prev_chr_list[note] = ch2

    logger.debug('note_min/max={}', (note_min, note_max))

    v_data: list[VisualLine] = [
        {'abs_time': abs_time,
         'chr': ''.join(chr_list[note_min:note_max+1])}
        for abs_time, chr_list in rows
    ]

    return {
        'note_min': note_min,
        'note_max': note_max,
        'data': v_data,
    }


def _format_note_ruler(note_min: int, note_max: int) -> list[str]:
    """ノート番号を縦3行で表す

    Returns
    -------
    lines: list of str
        3行
    """
    return [
        f'{" ":8}|'
        + ''.join(f'{n:03d}'[i] for n in range(note_min, note_max+1))
        + '|'
        for i in [0, 1, 2]
    ]


def format_visual(v_data: VisualData, channel_set: set[int]) -> str:
    """可視化データを文字列に整形する

    Parameters
    ----------
    v_data: VisualData
    channel_set: set of int

    Returns
    -------
    text: str
        末尾に改行は付かない
    """
    note_min = v_data['note_min']
    note_max = v_data['note_max']

    logger.debug('note_min/max={}', (note_min, note_max))
    logger.debug('channel_set={}', channel_set)

    border = '--------+' + '-' * (note_max - note_min + 1) + '+'
    ruler = _format_note_ruler(note_min, note_max)

    lines: list[str] = []
    lines += ruler
    lines.append(border)

    for v_ent in v_data['data']:
        lines.append(f'{v_ent["abs_time"]:08.3f}|{v_ent["chr"]}|')

    lines.append(border)
    lines += ruler

    lines.append('')

    for c in sorted(channel_set):
        lines.append(f'CH({c:2d}): {V_CHR_START[c]}--{V_CHR_STOP[c]}')

    return '\n'.join(lines)


def print_visual(v_data: VisualData, channel_set: set[int]) -> None:
    """可視化データを標準出力へ表示する

    `format_visual()` の薄いラッパー。

    Parameters
    ----------
    v_data: VisualData
    channel_set: set of int
    """
    print(format_visual(v_data, channel_set))

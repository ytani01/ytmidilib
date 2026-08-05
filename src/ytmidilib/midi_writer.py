#!/usr/bin/env python3
#
# (c) 2026 Yoichi Tanibayashi
#
"""
MIDI writer

`Parser.parse()` で得た `NoteInfo` のリストを MIDI ファイルへ書き戻す。
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2026/08'

import os
from typing import Any

import mido

from .midi_parser import DEFAULT_TEMPO, NoteInfo
from .midi_utils import NOTE_N
from .my_logger import get_logger

DEF_TICKS_PER_BEAT = 480

LOG = get_logger(__name__)


def transpose(note_info: list[NoteInfo], n: int) -> list[NoteInfo]:
    """移調する

    Parameters
    ----------
    note_info: list of NoteInfo
    n: int
        移調する半音数(負なら下げる)

    Returns
    -------
    out_data: list of NoteInfo
        新しいリスト。元のリストは変更しない

    Raises
    ------
    ValueError
        移調の結果、MIDIノート番号が 0 .. 127 の範囲外になる音がある場合。
        1音でも範囲外なら、移調全体を失敗させる
    """
    LOG.debug('n=%s', n)

    for ni in note_info:
        new_note = ni.note + n
        if not 0 <= new_note < NOTE_N:
            raise ValueError(
                f'note out of range: {ni.note} + {n} = {new_note}'
                f' (channel:{ni.channel} at {ni.abs_time:.3f})')

    return [NoteInfo(ni.abs_time, ni.channel, ni.note + n,
                     ni.velocity, ni.end_time)
            for ni in note_info]


def write(midi_file: str | os.PathLike[str], note_info: list[NoteInfo],
          ticks_per_beat: int = DEF_TICKS_PER_BEAT,
          tempo: int = DEFAULT_TEMPO) -> None:
    """`NoteInfo` のリストを MIDI ファイルへ書き出す

    絶対秒を tick に戻し、note_on / note_off の並びに展開する。
    全チャンネルを 1 トラックにまとめる。

    Parameters
    ----------
    midi_file: str or os.PathLike
        出力ファイル名
    note_info: list of NoteInfo
        `end_time` が設定済みであること。`None` の音は長さ 0 として扱う
    ticks_per_beat: int
        分解能 [tick/beat]
    tempo: int
        テンポ [usec/beat]。この値の set_tempo をファイル先頭に書く
    """
    LOG.debug('midi_file=%s, len(note_info)=%s', midi_file, len(note_info))
    LOG.debug('ticks_per_beat=%s, tempo=%s', ticks_per_beat, tempo)

    # (tick, velocity==0 が先, note) で並べる。
    # 同時刻では、消音を先に置いて、同じ note の再打鍵と衝突させない
    events: list[tuple[int, int, int, dict[str, Any]]] = []

    for ni in note_info:
        if ni.velocity == 0:
            continue

        on_tick = round(mido.second2tick(ni.abs_time, ticks_per_beat, tempo))
        end_time = ni.abs_time if ni.end_time is None else ni.end_time
        off_tick = round(mido.second2tick(end_time, ticks_per_beat, tempo))

        events.append((on_tick, 1, ni.note,
                       {'type': 'note_on', 'channel': ni.channel,
                        'note': ni.note, 'velocity': ni.velocity}))
        events.append((off_tick, 0, ni.note,
                       {'type': 'note_off', 'channel': ni.channel,
                        'note': ni.note, 'velocity': 0}))

    events.sort(key=lambda e: (e[0], e[1], e[2]))

    midi_obj = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    midi_obj.tracks.append(track)

    track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))

    prev_tick = 0
    for tick, _, _, msg in events:
        # 同時刻のイベントは delta=0 で続ける
        track.append(mido.Message(time=tick - prev_tick, **msg))
        prev_tick = tick

    track.append(mido.MetaMessage('end_of_track', time=0))

    midi_obj.save(midi_file)

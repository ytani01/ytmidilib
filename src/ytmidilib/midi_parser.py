#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
MIDI parser

MIDI ファイルを note 単位にパージングする。テキストによる可視化は
`midi_visual.py` にある (TODO-016)。
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2021/01'

import copy
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

import mido
from loguru import logger

from .midi_utils import DEFAULT_TEMPO

if TYPE_CHECKING:
    from .midi_visual import VisualData


@dataclass
class NoteInfo:
    """parsed MIDI data entity

    Attributes
    ----------
    abs_time: float
        曲頭からの開始時刻 [sec] >= 0
    channel: int
        0 .. 15
    note: int
        0 .. 127
    velocity: int
        0 .. 127
    end_time: float | None
        曲頭からの終了時刻 [sec] >= abs_time >= 0
    """
    abs_time: float
    channel: int
    note: int
    velocity: int
    end_time: float | None = None

    def __post_init__(self) -> None:
        """時刻を小数第3位に丸める"""
        self.abs_time = round(self.abs_time, 3)

        if self.end_time is not None:
            self.end_time = round(self.end_time, 3)

    def __str__(self) -> str:
        """
        Returns
        -------
        str_data: str
        """
        str_data = (f'start:{self.abs_time:08.3f}'
                    f' channel:{self.channel:02d}'
                    f' note:{self.note:03d}'
                    f' velocity:{self.velocity:03d}')

        if self.end_time is not None:
            str_data += (f' end:{self.end_time:08.3f}'
                         f' length:{self.length():05.2f}')

        return str_data

    def length(self) -> float:
        """
        Returns
        -------
        length: float
            length of note [sec]。`end_time` が未設定 (None) の場合は 0.0
        """
        if self.end_time is None:
            return 0.0

        return self.end_time - self.abs_time


class ParsedMidi(TypedDict):
    """`parse()` の戻り値"""
    channel_set: set[int]
    note_info: list[NoteInfo]


class NoteEvent(TypedDict):
    """1つの note の、鳴り始め/鳴り終わり"""
    note: int
    channel: int
    velocity: int


class TimedEvent(TypedDict):
    """同時刻の `NoteEvent` をまとめたもの。`mk_event_list()` の要素"""
    abs_time: float
    event: list[NoteEvent]


def parse1(midi_obj: mido.MidiFile,
           channel: list[int] | tuple[int, ...] | None = None
           ) -> tuple[set[int], list[NoteInfo]]:
    """
    parse MIDI format simply for subsequent parsing step

    全トラックを1本に合成し、tick を曲頭からの絶対秒に変換する。
    この段階では note_on / note_off が別々の NoteInfo として並ぶ。

    Parameters
    ----------
    midi_obj: mido.MidiFile
        MIDI file obj
    channel: list of int
        selected channel

    Returns
    -------
    channel_set: set of int
        チャンネルの絞り込み前に集めた、元ファイルの全チャンネル
    data: list of NoteInfo
    """
    merged_tracks = mido.merge_tracks(midi_obj.tracks)

    tpb = midi_obj.ticks_per_beat

    channel_set: set[int] = set()
    out_data: list[NoteInfo] = []
    abs_time = 0.0
    # MIDI 仕様の既定テンポ (120 BPM)。
    # set_tempo が無いファイルでも正しい秒数になるようにする。
    cur_tempo = DEFAULT_TEMPO

    for msg in merged_tracks:
        abs_time += mido.tick2second(msg.time, tpb, cur_tempo)

        if msg.type == 'set_tempo':
            cur_tempo = msg.tempo
            continue

        if msg.type == 'end_of_track':
            logger.debug('{}', msg.__dict__)
            break

        if msg.type not in ('note_on', 'note_off'):
            continue

        channel_set.add(msg.channel)
        if channel and msg.channel not in channel:
            continue

        velocity = msg.velocity if msg.type == 'note_on' else 0
        out_data.append(
            NoteInfo(abs_time, msg.channel, msg.note, velocity))

    return (channel_set, out_data)


def set_end_time(in_data: list[NoteInfo]) -> list[NoteInfo]:
    """set end time of NoteInfo

    (channel, note) ごとに開始待ちのインデックスを保持し、
    対応する note_off の時刻を開始側エントリの end_time に書き戻す。
    閉じられなかった note は、最終イベントの時刻で打ち切る。
    """
    logger.debug('')

    out_data = copy.deepcopy(in_data)
    note_start: dict[tuple[int, int], list[int]] = {}

    for i, ent in enumerate(out_data):
        key = (ent.channel, ent.note)

        if ent.velocity > 0:
            note_start.setdefault(key, []).append(i)
            continue

        # velocity == 0

        ent.end_time = ent.abs_time

        try:
            idx2 = note_start[key].pop(0)
        except (KeyError, IndexError) as ex:
            # 対応する note_on が無い note_off。壊れたファイルでは
            # 起きうるので、どの音かが分かる形で警告して読み飛ばす。
            logger.warning(
                '{}: no note_on for'
                ' channel:{:02d} note:{:03d} at {:08.3f} .. ignored',
                type(ex).__name__, ent.channel, ent.note, ent.abs_time)
            continue

        out_data[idx2].end_time = ent.abs_time

        if not note_start[key]:
            note_start.pop(key)

    if not out_data:
        return out_data

    # 閉じられなかった note は、最終イベントの時刻で打ち切る
    last_time = max(ent.abs_time for ent in out_data)

    for idx_list in note_start.values():
        for idx in idx_list:
            out_data[idx].end_time = last_time

    return out_data


def parse(midi_file: str | os.PathLike[str],
          channel: list[int] | tuple[int, ...] | None = None
          ) -> ParsedMidi:
    """
    parse MIDI data

    Parameters
    ----------
    midi_file: str or os.PathLike
        MIDI file name (`pathlib.Path` も可)
    channel: list of int or None for all channels
        MIDI channel

    Returns
    -------
    out_data: {
        'channel_set': set of int,
        'note_info': list of NoteInfo
    }
    """
    logger.debug('midi_file={}, channel={}', midi_file, channel)

    midi_obj = mido.MidiFile(midi_file)

    channel_set, data1 = parse1(midi_obj, channel)

    logger.debug('channel_set={}', channel_set)

    data2 = set_end_time(data1)

    return {
        'channel_set': channel_set,
        # remove velocity == 0
        'note_info': [d for d in data2 if d.velocity > 0],
    }


def mk_event_list(data: list[NoteInfo]) -> list[TimedEvent]:
    """note単位のデータを、時刻順のイベント列に変換する

    Parameters
    ----------
    data: list of NoteInfo
        `end_time` が未設定 (None) の音は、長さ 0 として扱う
        (`write()` と同じ。TODO-016)

    Returns
    -------
    merged_ev: list of TimedEvent
        同時刻のイベントは、同じ note が重ならない範囲でまとめられる
    """
    events: list[TimedEvent] = []

    for ni in data:
        if ni.velocity == 0:
            continue

        end_time = ni.abs_time if ni.end_time is None else ni.end_time

        events.append({
            'abs_time': ni.abs_time,
            'event': [{'note': ni.note,
                       'channel': ni.channel,
                       'velocity': ni.velocity}]
        })
        events.append({
            'abs_time': end_time,
            'event': [{'note': ni.note,
                       'channel': ni.channel,
                       'velocity': 0}]
        })

    sorted_ev = sorted(events, key=lambda x: x['abs_time'])

    merged_ev: list[TimedEvent] = []
    abs_time = -1.0
    for ev in sorted_ev:
        if ev['abs_time'] != abs_time:
            merged_ev.append(ev)
            abs_time = ev['abs_time']
            continue

        # 同時刻でも、同じ note が既にあればまとめない
        merge_flag = any(e1['note'] == ev['event'][0]['note']
                         for e1 in merged_ev[-1]['event'])

        if merge_flag:
            merged_ev.append(ev)
            continue

        merged_ev[-1]['event'].append(ev['event'][0])

    return merged_ev


class Parser:
    """
    MIDI parser

    実体はモジュールレベルの関数で、このクラスはそれを呼ぶだけ
    (TODO-016)。可視化のメソッドは `midi_visual.py` へ委譲する。
    """

    def __init__(self, debug: bool = False) -> None:
        """constructor

        Parameters
        ----------
        debug: bool
            互換のために残してある引数。ログの水準を決めるのは
            `mylog.loggerInit()` だけで、この引数は水準に影響しない
        """
        self._dbg = debug

    # 以下のメソッドは、同じ名前のモジュールレベルの関数を呼ぶだけ。
    # メソッドの中からの名前解決にクラスの名前空間は入らないので、
    # `parse1(...)` はモジュールレベルの関数を指す (再帰ではない)。

    def parse1(self, midi_obj: mido.MidiFile,
               channel: list[int] | tuple[int, ...] | None = None
               ) -> tuple[set[int], list[NoteInfo]]:
        """`parse1()` を呼ぶ"""
        return parse1(midi_obj, channel)

    def set_end_time(self, in_data: list[NoteInfo]) -> list[NoteInfo]:
        """`set_end_time()` を呼ぶ"""
        return set_end_time(in_data)

    def parse(self, midi_file: str | os.PathLike[str],
              channel: list[int] | tuple[int, ...] | None = None
              ) -> ParsedMidi:
        """`parse()` を呼ぶ"""
        return parse(midi_file, channel)

    def mk_event_list(self, data: list[NoteInfo]) -> list[TimedEvent]:
        """`mk_event_list()` を呼ぶ"""
        return mk_event_list(data)

    # 可視化。本体は `midi_visual.py` にある。
    # `midi_visual` はこのモジュールを import するので、
    # 循環 import を避けるためメソッドの中で import する。

    def mk_visual(self, data: list[NoteInfo]) -> "VisualData":
        """`midi_visual.mk_visual()` を呼ぶ"""
        from . import midi_visual

        return midi_visual.mk_visual(data)

    def format_visual(self, v_data: "VisualData",
                      channel_set: set[int]) -> str:
        """`midi_visual.format_visual()` を呼ぶ"""
        from . import midi_visual

        return midi_visual.format_visual(v_data, channel_set)

    def print_visual(self, v_data: "VisualData",
                     channel_set: set[int]) -> None:
        """`midi_visual.print_visual()` を呼ぶ"""
        from . import midi_visual

        midi_visual.print_visual(v_data, channel_set)

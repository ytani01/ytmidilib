#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
MIDI parser
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2021/01'

import copy
import os
from typing import Any, TypedDict

import mido
from loguru import logger

DEFAULT_TEMPO = 500000
"""MIDI 仕様の既定テンポ [usec/beat]。120 BPM 相当 (mido.bpm2tempo(120))。"""


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
    def __init__(self, abs_time: float, channel: int, note: int,
                 velocity: int, end_time: float | None = None) -> None:
        self.abs_time = round(abs_time, 3)
        self.channel = channel
        self.note = note
        self.velocity = velocity
        self.end_time = None if end_time is None else round(end_time, 3)

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

        if self.end_time:
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
    """`Parser.parse()` の戻り値"""
    channel_set: set[int]
    note_info: list[NoteInfo]


class VisualData(TypedDict):
    """`Parser.mk_visual()` の戻り値"""
    note_min: int
    note_max: int
    data: list[dict[str, Any]]


class Parser:
    """
    MIDI parser
    """
    MIDI_NOTE_N = 128

    V_CHR_ON = '|'
    V_CHR_OFF = ' '

    V_CHR_START = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    V_CHR_STOP = 'abcdefghijklmnopqrstuvwxyz'

    def __init__(self, debug: bool = False) -> None:
        """constructor

        Parameters
        ----------
        debug: bool
            互換のために残してある引数。ログの水準を決めるのは
            `mylog.loggerInit()` だけで、この引数は水準に影響しない
        """
        self._dbg = debug

        self._channel_set: set[int] = set()

    def parse1(self, midi_obj: mido.MidiFile,
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

    def set_end_time(self, in_data: list[NoteInfo]) -> list[NoteInfo]:
        """set end time of NoteInfo

        (channel, note) ごとに開始待ちのインデックスを保持し、
        対応する note_off の時刻を開始側エントリの end_time に書き戻す。
        閉じられなかった note は、最終イベントの時刻で打ち切る。
        """
        logger.debug('')

        out_data = copy.deepcopy(in_data)
        note_start: dict[tuple[int, int], list[int]] = {}

        ent = None
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

        if ent:
            for idx_list in note_start.values():
                for idx in idx_list:
                    out_data[idx].end_time = ent.abs_time

        return out_data

    def parse(self, midi_file: str | os.PathLike[str],
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

        self._channel_set, data1 = self.parse1(midi_obj, channel)

        logger.debug('channel_set={}', self._channel_set)

        data2 = self.set_end_time(data1)

        return {
            'channel_set': self._channel_set,
            # remove velocity == 0
            'note_info': [d for d in data2 if d.velocity > 0],
        }

    def mk_event_list(self, data: list[NoteInfo]) -> list[dict[str, Any]]:
        """note単位のデータを、時刻順のイベント列に変換する

        Parameters
        ----------
        data: list of NoteInfo

        Returns
        -------
        merged_ev: list of event
            同時刻のイベントは、同じ note が重ならない範囲でまとめられる
        """
        events: list[dict[str, Any]] = []

        for ni in data:
            if ni.velocity == 0:
                continue

            events.append({
                'abs_time': ni.abs_time,
                'event': [{'note': ni.note,
                           'channel': ni.channel,
                           'velocity': ni.velocity}]
            })
            events.append({
                'abs_time': ni.end_time,
                'event': [{'note': ni.note,
                           'channel': ni.channel,
                           'velocity': 0}]
            })

        sorted_ev = sorted(events, key=lambda x: x['abs_time'])

        merged_ev: list[dict[str, Any]] = []
        abs_time = -1
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

    def mk_visual(self, data: list[NoteInfo]) -> VisualData:
        """テキストによる可視化データを作る

        Parameters
        ----------
        data: list of NoteInfo
        """
        ev = self.mk_event_list(data)

        note_min = self.MIDI_NOTE_N - 1
        note_max = 0

        v_data: list[dict[str, Any]] = []
        prev_chr_list = [self.V_CHR_OFF] * self.MIDI_NOTE_N
        on_count = [0] * self.MIDI_NOTE_N

        for e in ev:
            v_data.append({'abs_time': e['abs_time'],
                           'chr': copy.deepcopy(prev_chr_list)})

            for e1 in e['event']:
                note = e1['note']

                note_min = min(note, note_min)
                note_max = max(note, note_max)

                if e1['velocity'] > 0:
                    ch1 = self.V_CHR_START[e1['channel']]
                    on_count[note] += 1
                    ch2 = self.V_CHR_ON
                else:
                    ch1 = self.V_CHR_STOP[e1['channel']]
                    on_count[note] -= 1
                    ch2 = self.V_CHR_ON if on_count[note] > 0 else self.V_CHR_OFF

                v_data[-1]['chr'][note] = ch1
                prev_chr_list[note] = ch2

        logger.debug('note_min/max={}', (note_min, note_max))

        for v_ent in v_data:
            v_ent['chr'] = ''.join(v_ent['chr'][note_min:note_max+1])

        return {
            'note_min': note_min,
            'note_max': note_max,
            'data': v_data,
        }

    def _format_note_ruler(self, note_min: int, note_max: int) -> list[str]:
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

    def format_visual(self, v_data: VisualData, channel_set: set[int]) -> str:
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
        ruler = self._format_note_ruler(note_min, note_max)

        lines: list[str] = []
        lines += ruler
        lines.append(border)

        for v_ent in v_data['data']:
            lines.append(f'{v_ent["abs_time"]:08.3f}|{v_ent["chr"]}|')

        lines.append(border)
        lines += ruler

        lines.append('')

        for c in sorted(channel_set):
            lines.append(
                f'CH({c:2d}): {self.V_CHR_START[c]}--{self.V_CHR_STOP[c]}')

        return '\n'.join(lines)

    def print_visual(self, v_data: VisualData, channel_set: set[int]) -> None:
        """可視化データを標準出力へ表示する

        `format_visual()` の薄いラッパー。

        Parameters
        ----------
        v_data: VisualData
        channel_set: set of int
        """
        print(self.format_visual(v_data, channel_set))

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
from typing import Any, BinaryIO

import mido

from .midi_parser import DEFAULT_TEMPO, NoteInfo
from .midi_utils import NOTE_N
from .my_logger import get_logger

DEF_TICKS_PER_BEAT = 480

DRUM_CHANNEL = 9
"""打楽器チャンネル(0始まり)。note が音の高さではなく楽器の種類を表す"""

LOG = get_logger(__name__)


def _shift_note(note: int, channel: int, n: int,
                clip: bool, drums: bool, where: str = '') -> tuple[int, bool]:
    """1つの note をずらす(`transpose()` / `transpose_file()` 共通)

    Parameters
    ----------
    note: int
        元の MIDIノート番号
    channel: int
        MIDIチャンネル
    n: int
        移調する半音数(負なら下げる)
    clip: bool
        True なら範囲外を 0 .. 127 に丸める。False なら `ValueError`
    drums: bool
        False なら channel 9 をずらさない(範囲チェック・クリップもしない)
    where: str
        `ValueError` のメッセージに足す位置情報

    Returns
    -------
    (new_note, clipped): tuple of (int, bool)
        `clipped` は、丸めたときだけ True

    Raises
    ------
    ValueError
        `clip` が False で、結果が 0 .. 127 の範囲外になる場合
    """
    if not drums and channel == DRUM_CHANNEL:
        return note, False

    new_note = note + n

    if 0 <= new_note < NOTE_N:
        return new_note, False

    if not clip:
        raise ValueError(
            f'note out of range: {note} + {n} = {new_note}'
            f' (channel:{channel}{where})')

    return min(max(new_note, 0), NOTE_N - 1), True


def transpose(note_info: list[NoteInfo], n: int,
              clip: bool = False, drums: bool = False) -> list[NoteInfo]:
    """移調する

    channel 9 (打楽器) の扱いは `drums` で決まる。既定ではずらさない
    (note が音の高さではなく楽器の種類を表すため)。ずらさない音は、
    範囲チェック・クリップの対象からも外れる。

    Parameters
    ----------
    note_info: list of NoteInfo
    n: int
        移調する半音数(負なら下げる)
    clip: bool
        False (既定) なら、範囲外の音が1つでもあれば `ValueError`。
        True なら 0 .. 127 に丸め、丸めたときだけ WARNING を1行出す
    drums: bool
        False (既定) なら channel 9 をずらさない。True なら全チャンネルを
        ずらす。`transpose_file()` と既定値・意味論を揃えてある

    Returns
    -------
    out_data: list of NoteInfo
        新しいリスト。元のリストは変更しない

    Raises
    ------
    ValueError
        `clip` が False で、移調の結果 MIDIノート番号が 0 .. 127 の
        範囲外になる音がある場合。1音でも範囲外なら、移調全体を失敗させる
    """
    LOG.debug('n=%s, clip=%s, drums=%s', n, clip, drums)

    out_data: list[NoteInfo] = []
    clip_count = 0

    for ni in note_info:
        new_note, clipped = _shift_note(
            ni.note, ni.channel, n, clip, drums,
            f' at {ni.abs_time:.3f}')

        if clipped:
            clip_count += 1

        out_data.append(NoteInfo(ni.abs_time, ni.channel, new_note,
                                 ni.velocity, ni.end_time))

    if clip_count:
        LOG.warning('clipped %s note(s) into 0 .. %s',
                    clip_count, NOTE_N - 1)

    return out_data


def transpose_file(src: str | os.PathLike[str] | BinaryIO,
                   dst: str | os.PathLike[str] | BinaryIO,
                   n: int,
                   clip: bool = False, drums: bool = False) -> None:
    """MIDIファイルを移調する

    `note_on` / `note_off` の `note` **だけ**をずらす。他のメッセージ・
    トラック構成・`ticks_per_beat`・ファイルの type は変更しない
    (読み込んだファイルをその場で書き換えて保存するため)。

    ただし、`mido` による再直列化を経るので、running status や delta の
    符号化までバイト単位で一致することは保証しない。

    channel 9 (打楽器) の扱いは `transpose()` と同じ。

    Parameters
    ----------
    src: str or os.PathLike or file-like
        入力。パス、または読み込み可能なバイナリ file-like (`io.BytesIO` 等)
    dst: str or os.PathLike or file-like
        出力。パス、または書き込み可能なバイナリ file-like
    n: int
        移調する半音数(負なら下げる)
    clip: bool
        False (既定) なら、範囲外の音が1つでもあれば `ValueError`。
        True なら 0 .. 127 に丸め、丸めたときだけ WARNING を1行出す
    drums: bool
        False (既定) なら channel 9 をずらさない。True なら全チャンネルを
        ずらす

    Raises
    ------
    ValueError
        `clip` が False で、移調の結果 MIDIノート番号が 0 .. 127 の
        範囲外になる音がある場合。1音でも範囲外なら、移調全体を失敗させる
        (`dst` には何も書かない)
    """
    LOG.debug('n=%s, clip=%s, drums=%s', n, clip, drums)

    if isinstance(src, (str, os.PathLike)):
        midi_obj = mido.MidiFile(filename=os.fspath(src))
    else:
        midi_obj = mido.MidiFile(file=src)

    clip_count = 0

    for track in midi_obj.tracks:
        for msg in track:
            if msg.type not in ('note_on', 'note_off'):
                continue

            new_note, clipped = _shift_note(
                msg.note, msg.channel, n, clip, drums)

            if clipped:
                clip_count += 1

            msg.note = new_note

    if clip_count:
        LOG.warning('clipped %s note(s) into 0 .. %s',
                    clip_count, NOTE_N - 1)

    if isinstance(dst, (str, os.PathLike)):
        midi_obj.save(filename=os.fspath(dst))
    else:
        midi_obj.save(file=dst)


def write(midi_file: str | os.PathLike[str], note_info: list[NoteInfo],
          ticks_per_beat: int = DEF_TICKS_PER_BEAT,
          tempo: int = DEFAULT_TEMPO) -> None:
    """`NoteInfo` のリストを MIDI ファイルへ書き出す

    絶対秒を tick に戻し、note_on / note_off の並びに展開する。
    全チャンネルを 1 トラックにまとめる。

    **`NoteInfo` が持たないものは書き出されない。** 具体的には:

    - `program_change` (音色) — すべて既定の音色になる
    - `control_change` (音量・ペダルなど)
    - `pitch_bend`
    - メタメッセージ (`track_name` / `time_signature` など)
    - トラック構成 (全チャンネルが 1 トラックに潰れる)
    - テンポ変化 (引数 `tempo` の `set_tempo` 1つに潰れる)

    したがって `parse()` → `write()` は「元のファイルに戻る」往復では
    ない。元のファイルを保ったまま移調したい場合は `transpose_file()`
    を使う。

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

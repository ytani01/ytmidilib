#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
MIDI utilities
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2020'

from loguru import logger

FREQ_BASE = 440
NOTE_BASE = 69
NOTE_N = 128

DEFAULT_TEMPO = 500000
"""MIDI 仕様の既定テンポ [usec/beat]。120 BPM 相当 (mido.bpm2tempo(120))。

パーサ固有のものではなく MIDI 仕様の既定値なので、ここに置く
(`midi_writer.write()` の既定値でもある。TODO-016)。
"""

DRUM_CHANNEL = 9
"""打楽器チャンネル(0始まり)。note が音の高さではなく楽器の種類を表す。

`midi_writer.py` 固有のものではなく MIDI 仕様の定数で、`__main__.py`
（`--drums` のヘルプ）と `tests/conftest.py` からも使うので、ここに置く
(`DEFAULT_TEMPO` と同じ理由。TODO-023)。
"""


def note2freq(note: int) -> float:
    """MIDI ノート番号を周波数に変換する

    Parameters
    ----------
    note: int
        MIDI ノート番号 (A4 = 69 = 440Hz)

    Returns
    -------
    freq: float
        周波数 [Hz]
    """
    logger.debug('note={}', note)

    return FREQ_BASE * 2.0 ** ((note - NOTE_BASE) / 12.0)


def clip_range[T: (int, float)](num: T, n_min: T, n_max: T) -> T:
    """num を n_min .. n_max の範囲に丸める

    Parameters
    ----------
    num: int or float
    n_min: int or float
    n_max: int or float

    Returns
    -------
    clipped: int or float
        num と同じ型
    """
    return min(max(num, n_min), n_max)

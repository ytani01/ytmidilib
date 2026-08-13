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


def note2freq(note: int) -> float:
    """MIDI note number to frequency

    Parameters
    ----------
    note: int
        MIDI note number (A4 = 69 = 440Hz)

    Returns
    -------
    freq: float
        frequency [Hz]
    """
    logger.debug('note={}', note)

    return FREQ_BASE * 2.0 ** ((note - NOTE_BASE) / 12.0)

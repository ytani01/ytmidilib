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

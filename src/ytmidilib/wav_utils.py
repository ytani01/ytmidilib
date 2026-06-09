#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
Wav file utilites
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2020'

import wave
import array
import time
import numpy as np
import pygame
from .my_logger import get_logger


class Wav:
    """Wav

    Attributes
    ----------
    attr1: type(int|str|list of str ..)
        description
    """
    DEF_SEC = 1.0  # sec
    DEF_RATE = 44100  # Hz
    VOL_MAX = 1.0
    VOL_MIN = 0.0
    DEF_VOL = 0.25

    def __init__(self, freq, sec=DEF_SEC, rate=DEF_RATE, debug=False):
        """constructor

        Parameters
        ----------
        """
        self._dbg = debug
        self.__log = get_logger(__class__.__name__, self._dbg)
        self.__log.debug('freq,sec,rate=%s', (freq, sec, rate))

        self._freq = freq
        self._sec = sec
        self._rate = rate

        self.wav = self.mk_wav()

    def mk_wav(self):
        """method1

        Parameters
        ----------
        """
        self.__log.debug('')

        # サンプリングする位置(秒)のarray
        sample_sec = np.arange(self._rate * self._sec) / self._rate

        # -32767 .. 32767 の sin波
        amplitude = 32767  # 振幅
        sin_wave1 = amplitude * np.sin(
            2 * np.pi * self._freq * sample_sec)

        # [Important!]
        #   fade-in/outすることで、耳障りなブツブツ音を軽減
        #
        # [TBD]
        #   前後のフェードする割合は、self._secに応じて片方が
        #   いいかも?
        #
        fade_len = int(sin_wave1.size * 0.01)
        slope = (np.arange(fade_len)) / fade_len
        sin_wave1[:fade_len] = sin_wave1[:fade_len] * slope
        fade_len = int(sin_wave1.size * 0.4)
        slope = ((fade_len - 1) - np.arange(fade_len)) / fade_len
        sin_wave1[-fade_len:] = sin_wave1[-fade_len:] * slope

        # int16に変換
        sin_wave2 = np.array(sin_wave1, dtype=np.int16)

        return sin_wave2

    def save(self, outfile):
        """
        outfile: str
        """
        self.__log.debug('outfile=%s', outfile)

        w_write = wave.Wave_write(outfile)
        w_write.setparams((
            1, 2, self._rate, len(self.wav), 'NONE', 'not compressed'))
        w_write.writeframes(array.array('h', self.wav).tobytes())
        w_write.close()

    def play(self, vol=DEF_VOL):
        """
        Parameters
        ----------
        vol: float
        """
        self.__log.debug('vol=%s', vol)

        if vol > self.VOL_MAX:
            vol = self.VOL_MAX
            self.__log.warning('fix: vol=%s', vol)

        if vol < self.VOL_MIN:
            vol = self.VOL_MIN
            self.__log.warning('fix: vol=%s', vol)

        snd = pygame.sndarray.make_sound(self.wav)
        # maxtime = int(self._sec * 950)

        snd.set_volume(vol)
        # snd.play(fade_ms=20, maxtime=maxtime)
        snd.play()
        time.sleep(self._sec)

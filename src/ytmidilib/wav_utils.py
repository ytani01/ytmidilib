#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
Wav file utilites
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2020'

import array
import time
import wave

import numpy as np
import pygame
from numpy.typing import NDArray

from .my_logger import get_logger


class Wav:
    """指定された周波数の sin波 音源データを生成/再生/保存する

    Attributes
    ----------
    wav: NDArray[np.int16]
        生成された音源データ(モノラル)
    """
    DEF_SEC = 1.0  # sec
    DEF_RATE = 44100  # Hz
    VOL_MAX = 1.0
    VOL_MIN = 0.0
    DEF_VOL = 0.25

    # フェードさせる長さ(全体に対する割合)
    FADE_IN_RATIO = 0.01
    FADE_OUT_RATIO = 0.4

    AMPLITUDE = 32767  # 振幅 (int16の最大値)

    def __init__(self, freq: float, sec: float = DEF_SEC,
                 rate: int = DEF_RATE, debug: bool = False) -> None:
        """constructor

        Parameters
        ----------
        freq: float
            周波数 [Hz]
        sec: float
            長さ [sec]
        rate: int
            サンプリングレート [Hz]
        """
        self._dbg = debug
        self._log = get_logger(self.__class__.__name__, self._dbg)
        self._log.debug('freq,sec,rate=%s', (freq, sec, rate))

        self._freq = freq
        self._sec = sec
        self._rate = rate

        self.wav = self.mk_wav()

    def mk_wav(self) -> NDArray[np.int16]:
        """sin波の音源データを生成する

        Returns
        -------
        wav: NDArray[np.int16]
        """
        self._log.debug('')

        # サンプリングする位置(秒)のarray
        sample_sec = np.arange(self._rate * self._sec) / self._rate

        # -32767 .. 32767 の sin波
        sin_wave = self.AMPLITUDE * np.sin(
            2 * np.pi * self._freq * sample_sec)

        # [Important!]
        #   fade-in/outすることで、耳障りなブツブツ音を軽減
        #
        # [TBD]
        #   前後のフェードする割合は、self._secに応じて片方が
        #   いいかも?
        #
        in_len = int(sin_wave.size * self.FADE_IN_RATIO)
        sin_wave[:in_len] *= np.arange(in_len) / in_len

        out_len = int(sin_wave.size * self.FADE_OUT_RATIO)
        sin_wave[-out_len:] *= (
            (out_len - 1) - np.arange(out_len)) / out_len

        return np.array(sin_wave, dtype=np.int16)

    def save(self, outfile: str) -> None:
        """音源データを wav形式 のファイルに保存する

        Parameters
        ----------
        outfile: str
            出力ファイル名
        """
        self._log.debug('outfile=%s', outfile)

        with wave.open(outfile, 'wb') as w_write:
            w_write.setparams((
                1, 2, self._rate, len(self.wav), 'NONE', 'not compressed'))
            w_write.writeframes(array.array('h', self.wav).tobytes())

    def play(self, vol: float = DEF_VOL) -> None:
        """音源データを再生し、鳴り終わるまで待つ

        Parameters
        ----------
        vol: float
            音量 (VOL_MIN .. VOL_MAX)
        """
        self._log.debug('vol=%s', vol)

        fixed_vol = min(max(vol, self.VOL_MIN), self.VOL_MAX)
        if fixed_vol != vol:
            self._log.warning('fix: vol=%s -> %s', vol, fixed_vol)

        snd = pygame.sndarray.make_sound(self.wav)
        snd.set_volume(fixed_vol)
        snd.play()
        time.sleep(self._sec)

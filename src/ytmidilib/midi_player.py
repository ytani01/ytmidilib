#
# (c) 2020 Yoichi Tanibayashi
#
"""
MIDI player
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2020'

import queue
import threading
import time

import pygame

from .midi_parser import NoteInfo, ParsedData
from .midi_utils import note2freq
from .my_logger import get_logger
from .wav_utils import Wav


class Player:
    """
    パージング済みのMIDIデータを、sin波の音源で再生する
    """
    DEF_RATE = 22050  # Hz .. sampling rate

    SEC_MIN = 0.02  # sec
    SEC_MAX = 1.20  # sec

    FIRST_DELAY_MAX = 3  # sec

    def __init__(self, rate: int = DEF_RATE, debug: bool = False) -> None:
        """ Constructor

        Parameters
        ----------
        rate: int
            サンプリングレート [Hz]
        """
        self._dbg = debug
        self._log = get_logger(self.__class__.__name__, self._dbg)
        self._log.debug('rate=%s', rate)

        self._rate = rate

        pygame.mixer.init(frequency=self._rate, channels=1)

        self._snd: dict[tuple[int, float], pygame.mixer.Sound] = {}

    @staticmethod
    def within_range(num: float, n_min: float, n_max: float) -> float:
        """
        keep num within range
        """
        return min(max(num, n_min), n_max)

    def snd_key(self, note_data: NoteInfo,
                sec_min: float, sec_max: float) -> tuple[int, float]:
        """音源キャッシュのキーを求める

        長さを丸めることで、生成する音源の種類数を抑える。

        Returns
        -------
        key: tuple
            (note_num, 丸めた長さ)
        """
        sec = self.within_range(note_data.length(), sec_min, sec_max)

        if sec > 0.5:
            # 0.02 単位に丸める
            key_sec = round(round(sec / 2.0, 2) * 2, 2)
        else:
            key_sec = round(sec, 2)

        return (note_data.note, key_sec)

    def mk_wav(self, in_data: list[NoteInfo],
               sec_min: float, sec_max: float
               ) -> dict[tuple[int, float], pygame.mixer.Sound]:
        """再生に必要な音源データを、あらかじめ全て生成しておく
        """
        for note_info in in_data:
            if note_info.velocity == 0:
                continue

            key = self.snd_key(note_info, sec_min, sec_max)

            if key in self._snd:
                continue

            freq = note2freq(note_info.note)
            sec = self.within_range(note_info.length(), sec_min, sec_max)

            wav = Wav(freq, sec, self._rate).wav

            self._snd[key] = pygame.sndarray.make_sound(wav)

        return self._snd

    def play_sound(self, note_info: NoteInfo,
                   sec_min: float, sec_max: float) -> None:
        """
        play sound
        """
        key = self.snd_key(note_info, sec_min, sec_max)

        snd = self._snd[key]
        snd.set_volume(note_info.velocity / 128 / 8)
        snd.play()

    def play_th(self, note_q: "queue.Queue[NoteInfo | None]",
                sec_min: float, sec_max: float) -> None:
        """
        play thread

        キューから受け取ったnoteを発音する。None で終了。
        """
        my_clock_base = -1.0

        while True:
            note_info = note_q.get()

            if not note_info:
                break

            if my_clock_base < 0:
                my_clock_base = time.time() - note_info.abs_time

            now = time.time() - my_clock_base

            self.play_sound(note_info, sec_min, sec_max)
            print(f'{now:08.3f} / {note_info}')

    def play(self, parsed_midi: ParsedData,
             pos_sec: float = 0.0,
             sec_min: float = SEC_MIN, sec_max: float = SEC_MAX) -> None:
        """
        play parsed midi data

        メインスレッドが time.sleep() でスケジューリングし、
        実際の発音はワーカースレッドが行う。
        理想時刻と実時刻のずれ(clock_delay)を次のsleepから引くことで、
        ずれの累積を防ぐ。

        Parameters
        ----------
        parsed_midi: {
            'channel_set': set of int,
            'note_info': list of NoteInfo
        }
        pos_sec: float
            seek position in sec
        sec_min: float
            min sound length
        sec_max: float
            max sound length
        """
        self._log.debug('parsed_midi[channel_set]=%s,',
                        parsed_midi['channel_set'])
        self._log.debug('length of parsed_midi[note_info]=%s',
                        len(parsed_midi['note_info']))
        self._log.debug('pos_sec=%s', pos_sec)
        self._log.debug('sec: %s .. %s', sec_min, sec_max)

        data = parsed_midi['note_info']

        snd = self.mk_wav(data, sec_min, sec_max)
        self._log.info('len(snd)=%s', len(snd))

        note_q: "queue.Queue[NoteInfo | None]" = queue.Queue()

        th = threading.Thread(
            target=self.play_th,
            args=(note_q, sec_min, sec_max),
            daemon=True)
        th.start()

        abs_time = 0.0
        my_clock_base = -1.0
        clock_delay = 0.0

        for i, note_info in enumerate(data):
            if note_info.abs_time < pos_sec:
                continue

            self._log.debug('(%4d) %s', i, note_info)

            delay = note_info.abs_time - abs_time
            self._log.debug('delay=%s', delay)

            if i == 0 and delay > self.FIRST_DELAY_MAX:
                self._log.warning('delay:%s too long ..', delay)
                delay = self.FIRST_DELAY_MAX
                self._log.warning('[fix] delay=%s', delay)

            if delay > 0:
                delay -= clock_delay  # time adjustment
                time.sleep(max(delay, 0.001))

            # calc clock_delay
            if my_clock_base < 0:
                my_clock_base = time.time() - note_info.abs_time

            now = time.time() - my_clock_base

            clock_delay = now - note_info.abs_time
            self._log.debug('%8.3f / %8.3f clock_delay=%s',
                            now, note_info.abs_time, clock_delay)

            abs_time = note_info.abs_time
            self._log.debug('abs_time=%s', abs_time)

            if note_info.velocity == 0:
                continue

            note_q.put(note_info)

        note_q.put(None)
        th.join()
        time.sleep(.5)

        print('end music')

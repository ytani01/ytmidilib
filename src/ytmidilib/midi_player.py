#
# (c) 2020 Yoichi Tanibayashi
#
"""
MIDI player
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2020'

import time
import threading
import queue
import pygame
from .wav_utils import Wav
from .midi_utils import note2freq
from .my_logger import get_logger


class Player:
    """
    MIDI parser for Music Box
    """
    DEF_RATE = 22050  # Hz .. sampling rate

    SEC_MIN = 0.02  # sec
    SEC_MAX = 1.20  # sec

    FIRST_DELAY_MAX = 3  # sec

    def __init__(self, rate=DEF_RATE, debug=False):
        """ Constructor

        Parameters
        ----------
        midi_file: str
            file name of MIDI file
        """
        self._dbg = debug
        self.__log = get_logger(__class__.__name__, self._dbg)
        self.__log.debug('rate=%s', rate)

        self._rate = rate

        self._sec_min = self.SEC_MIN
        self._sec_max = self.SEC_MAX

        pygame.mixer.init(frequency=self._rate, channels=1)

        self._snd = {}

    @staticmethod
    def within_range(num, n_min, n_max):
        """
        keep n within range
        """
        return min(max(num, n_min), n_max)

    def snd_key(self, note_data, sec_min, sec_max):
        """
        Returns
        -------
        key: tuple of int
            (note_num, sec)
        """
        sec = self.within_range(note_data.length(), sec_min, sec_max)

        if sec > 0.5:
            # 0.02 単位に丸める
            key_sec = round(round(sec / 2.0, 2) * 2, 2)
        else:
            key_sec = round(sec, 2)

        key = (note_data.note, key_sec)
        return key

    def mk_wav(self, in_data, sec_min, sec_max):
        """
        make sound data
        """
        for i, note_info in enumerate(in_data):
            if note_info.velocity == 0:
                continue

            key = self.snd_key(note_info, sec_min, sec_max)

            if key in self._snd.keys():
                continue

            # self.__log.debug('(%4d) new key: %s', i, key)

            freq = note2freq(note_info.note)
            sec = self.within_range(note_info.length(), sec_min, sec_max)

            wav = Wav(freq, sec, self._rate).wav

            self._snd[key] = pygame.sndarray.make_sound(wav)

        return self._snd

    def play_sound(self, note_info, sec_min, sec_max) -> None:
        """
        play sound
        """
        key = self.snd_key(note_info, sec_min, sec_max)

        snd = self._snd[key]
        vol = note_info.velocity / 128 / 8
        # maxtime = int(sec_max * self.SND_PLAY_FACTOR)

        snd.set_volume(vol)
        # snd.play(fade_ms=5, maxtime=maxtime)
        snd.play()

    def play_th(self, note_q, sec_min, sec_max):
        """
        play thread
        """
        my_clock_base = -1

        while True:
            note_info = note_q.get()

            if not note_info:
                break

            if my_clock_base < 0:
                my_clock_base = time.time() - note_info.abs_time

            now = time.time() - my_clock_base

            self.play_sound(note_info, sec_min, sec_max)
            print('%08.3f / %s' % (now, note_info))

    def play(self, parsed_midi,  # pylint: disable=too-many-locals
             pos_sec=0.0,
             sec_min=SEC_MIN, sec_max=SEC_MAX) -> None:
        """
        play parsed midi data

        Parameters
        ----------
        parsed_data: {
            'channel_set': set of int,
            'note_info': list of NoteInfo
        }
        pos_sec: float
            seek position in sec
        sec_min: int
            min sound length
        sec_max: int
            max sound length
        """
        self.__log.debug('parsed_midi[channel_set]=%s,',
                         parsed_midi['channel_set'])
        self.__log.debug('length of parsed_midi[data]=%s',
                         len(parsed_midi['note_info']))
        self.__log.debug('pos_sec=%s', pos_sec)
        self.__log.debug('sec: %s .. %s', sec_min, sec_max)

        data = parsed_midi['note_info']

        snd = self.mk_wav(parsed_midi['note_info'], sec_min, sec_max)
        self.__log.info('len(snd)=%s', len(snd))

        abs_time = 0

        note_q: queue.Queue = queue.Queue()

        th = threading.Thread(  # pylint: disable=invalid-name
            target=self.play_th,
            args=(note_q, sec_min, sec_max),
            daemon=True)
        th.start()

        my_clock_base = -1.0
        now = 0.0
        clock_delay = 0.0

        for i, note_info in enumerate(data):
            if note_info.abs_time < pos_sec:
                continue

            self.__log.debug('(%4d) %s', i, note_info)

            delay = note_info.abs_time - abs_time
            self.__log.debug('delay=%s', delay)

            if i == 0 and delay > self.FIRST_DELAY_MAX:
                self.__log.warning('delay:%s too long ..', delay)
                delay = self.FIRST_DELAY_MAX
                self.__log.warning('[fix] delay=%s', delay)

            if delay > 0:
                delay -= clock_delay  # time adjustment
                if delay <= 0:
                    delay = 0.001

                time.sleep(delay)

            # calc clock_delay
            if my_clock_base < 0:
                my_clock_base = time.time() - note_info.abs_time

            now = time.time() - my_clock_base

            clock_delay = now - note_info.abs_time
            self.__log.debug('%8.3f / %8.3f clock_delay=%s',
                             now, note_info.abs_time, clock_delay)

            abs_time = note_info.abs_time
            self.__log.debug('abs_time=%s', abs_time)

            if note_info.velocity == 0:
                continue

            note_q.put(note_info)

        note_q.put(None)
        th.join()
        time.sleep(.5)

        print('end music')

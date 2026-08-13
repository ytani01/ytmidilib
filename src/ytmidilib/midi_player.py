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
from loguru import logger

from .midi_parser import NoteInfo, ParsedMidi
from .midi_utils import clip_range, note2freq
from .wav_utils import Wav
from .wav_utils import init_mixer as wav_init_mixer
from .wav_utils import quit_mixer as wav_quit_mixer


class Player:
    """
    パージング済みのMIDIデータを、sin波の音源で再生する
    """
    DEF_RATE = 22050  # Hz .. sampling rate

    SEC_MIN = 0.02  # sec
    SEC_MAX = 1.20  # sec

    FIRST_DELAY_MAX = 3  # sec

    VELOCITY_MAX = 128
    """velocity(0..127)を 0.0 .. 1.0 未満の音量に正規化するときの分母"""

    VOLUME_ATTENUATION = 8
    """複数音が重なっても割れないよう、音量をさらに抑える係数"""

    def __init__(self, rate: int = DEF_RATE, debug: bool = False) -> None:
        """ コンストラクタ

        Parameters
        ----------
        rate: int
            サンプリングレート [Hz]
        debug: bool
            互換のために残してある引数。ログの水準を決めるのは
            `mylog.loggerInit()` だけで、この引数は水準に影響しない
        """
        self._dbg = debug
        logger.debug('rate={}', rate)

        self._rate = rate

        self._snd: dict[tuple[int, float], pygame.mixer.Sound] = {}

        self._stop_event = threading.Event()
        self._play_thread: threading.Thread | None = None

    def init_mixer(self) -> None:
        """pygame の mixer を初期化する

        音源生成/再生の直前に呼ばれる。初期化済みなら何もしないので、
        他所（`WavApp` など）が先に初期化していても二重にはならない。
        音声デバイスが無い環境では、ここで `pygame.error` になる。
        `wav_utils.init_mixer()` の薄いラッパー。
        """
        wav_init_mixer(self._rate)

    def close(self) -> None:
        """再生を止め、mixer を終了し、生成済みの音源を捨てる"""
        logger.debug('')

        self.stop()

        self._snd = {}

        wav_quit_mixer()

    def __enter__(self) -> "Player":
        return self

    def __exit__(self, exc_type: object, exc_value: object,
                 traceback: object) -> None:
        self.close()

    @staticmethod
    def within_range(num: float, n_min: float, n_max: float) -> float:
        """num を n_min .. n_max の範囲に丸める

        `midi_utils.clip_range()` の薄いラッパー(呼び出し側の互換のため
        staticmethod として残してある)
        """
        return clip_range(num, n_min, n_max)

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
        self.init_mixer()

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
        音を鳴らす
        """
        key = self.snd_key(note_info, sec_min, sec_max)

        snd = self._snd[key]
        snd.set_volume(
            note_info.velocity / self.VELOCITY_MAX / self.VOLUME_ATTENUATION)
        snd.play()

    def play_th(self, note_q: "queue.Queue[NoteInfo | None]",
                sec_min: float, sec_max: float) -> None:
        """
        発音スレッド

        キューから受け取ったnoteを発音する。None で終了。
        stop() が呼ばれた場合も、残りを鳴らさずに終了する。
        """
        my_clock_base = -1.0

        while True:
            note_info = note_q.get()

            if not note_info or self._stop_event.is_set():
                break

            if my_clock_base < 0:
                my_clock_base = time.time() - note_info.abs_time

            now = time.time() - my_clock_base

            self.play_sound(note_info, sec_min, sec_max)
            logger.debug('{:08.3f} / {}', now, note_info)

    def play(self, parsed_midi: ParsedMidi,
             pos_sec: float = 0.0,
             sec_min: float = SEC_MIN, sec_max: float = SEC_MAX,
             block: bool = True) -> None:
        """
        解析済みの MIDI データを再生する

        音源の生成 (`mk_wav()`) は `block` によらず、この呼び出しの中で
        先に済ませる。音声デバイスが無ければ、ここでエラーになる。

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
        block: bool
            True なら鳴り終わるまで待つ。
            False なら別スレッドで再生し、すぐに戻る

        Raises
        ------
        RuntimeError
            再生中に呼ばれた場合
        """
        logger.debug('parsed_midi[channel_set]={},',
                     parsed_midi['channel_set'])
        logger.debug('length of parsed_midi[note_info]={}',
                     len(parsed_midi['note_info']))
        logger.debug('pos_sec={}', pos_sec)
        logger.debug('sec: {} .. {}', sec_min, sec_max)
        logger.debug('block={}', block)

        if self.is_playing():
            raise RuntimeError('already playing: call stop() first')

        data = parsed_midi['note_info']

        snd = self.mk_wav(data, sec_min, sec_max)
        logger.debug('len(snd)={}', len(snd))

        # 前回の stop() を持ち越さない
        self._stop_event.clear()

        if block:
            self._play_main(data, pos_sec, sec_min, sec_max)
            return

        self._play_thread = threading.Thread(
            target=self._play_main,
            args=(data, pos_sec, sec_min, sec_max),
            daemon=True)
        self._play_thread.start()

    def is_playing(self) -> bool:
        """
        Returns
        -------
        playing: bool
            `play(block=False)` で始めた再生が続いているか
        """
        return self._play_thread is not None and self._play_thread.is_alive()

    def stop(self) -> None:
        """再生を止める

        スケジューリングのループと発音のワーカーの両方に終了を伝え、
        鳴っている音も止める。`play()` を呼び直せば再度再生できる。
        """
        logger.debug('')

        self._stop_event.set()

        if self._play_thread is not None:
            self._play_thread.join()
            self._play_thread = None

        if pygame.mixer.get_init():
            pygame.mixer.stop()

    def _play_main(self, data: list[NoteInfo], pos_sec: float,
                   sec_min: float, sec_max: float) -> None:
        """再生の本体

        メインスレッドが time.sleep() でスケジューリングし、
        実際の発音はワーカースレッドが行う。
        理想時刻と実時刻のずれ(clock_delay)を次のsleepから引くことで、
        ずれの累積を防ぐ。
        """
        note_q: queue.Queue[NoteInfo | None] = queue.Queue()

        th = threading.Thread(
            target=self.play_th,
            args=(note_q, sec_min, sec_max),
            daemon=True)
        th.start()

        abs_time = pos_sec
        my_clock_base = -1.0
        clock_delay = 0.0
        first_play = True

        for i, note_info in enumerate(data):
            if self._stop_event.is_set():
                logger.debug('stopped')
                break

            if note_info.abs_time < pos_sec:
                continue

            logger.debug('({:4d}) {}', i, note_info)

            delay = note_info.abs_time - abs_time
            logger.debug('delay={}', delay)

            if first_play and delay > self.FIRST_DELAY_MAX:
                logger.warning('delay:{} too long ..', delay)
                delay = self.FIRST_DELAY_MAX
                logger.warning('[fix] delay={}', delay)
            first_play = False

            if delay > 0:
                delay -= clock_delay  # time adjustment
                # stop() にすぐ反応できるよう、sleep ではなく wait で待つ
                self._stop_event.wait(max(delay, 0.001))

            # calc clock_delay
            if my_clock_base < 0:
                my_clock_base = time.time() - note_info.abs_time

            now = time.time() - my_clock_base

            clock_delay = now - note_info.abs_time
            logger.debug('{:8.3f} / {:8.3f} clock_delay={}',
                         now, note_info.abs_time, clock_delay)

            abs_time = note_info.abs_time
            logger.debug('abs_time={}', abs_time)

            if note_info.velocity == 0:
                continue

            note_q.put(note_info)

        note_q.put(None)
        th.join()

        # 最後の音の余韻を待つ
        self._stop_event.wait(.5)

        logger.debug('end music')

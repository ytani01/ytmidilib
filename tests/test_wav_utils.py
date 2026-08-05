#
# (c) 2026 Yoichi Tanibayashi
#
"""
`ytmidilib.wav_utils` のテスト

**再生 (`play()`) はテストしない**(音声デバイスが要るため)。
音源データの生成と保存までを見る。
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2026/08'

import wave
from pathlib import Path

import numpy as np
import pytest

from ytmidilib import Wav

RATE = 8000
"""テスト用のサンプリングレート [Hz](速く回すために低めにする)"""

FREQ = 440.0
SEC = 0.5


def test_mk_wav_shape() -> None:
    """サンプル数とデータ型"""
    wav = Wav(FREQ, SEC, RATE).wav

    assert len(wav) == int(RATE * SEC)
    assert wav.dtype == np.int16


def test_mk_wav_amplitude() -> None:
    """振幅は AMPLITUDE を超えない(int16 で溢れない)"""
    wav = Wav(FREQ, SEC, RATE).wav

    assert int(np.max(np.abs(wav))) <= Wav.AMPLITUDE
    # 音として意味のある大きさにはなっている
    assert int(np.max(np.abs(wav))) > Wav.AMPLITUDE // 2


def test_mk_wav_fade() -> None:
    """前後にフェードが掛かっている

    これを外すと、再生時に耳障りなブツブツ音が出る。
    """
    wav = Wav(FREQ, SEC, RATE).wav

    # 両端は完全に 0
    assert wav[0] == 0
    assert wav[-1] == 0

    peak = int(np.max(np.abs(wav)))
    in_len = int(len(wav) * Wav.FADE_IN_RATIO)
    out_len = int(len(wav) * Wav.FADE_OUT_RATIO)

    # 端の部分は、全体の最大振幅より確実に小さい
    assert int(np.max(np.abs(wav[:in_len]))) < peak
    assert int(np.max(np.abs(wav[-out_len:]))) < peak

    # 末尾は単調に小さくなっていく(区間ごとの最大値で見る)
    tail = wav[-out_len:]
    block = out_len // 4
    tail_peaks = [int(np.max(np.abs(tail[i * block:(i + 1) * block])))
                  for i in range(4)]
    assert tail_peaks == sorted(tail_peaks, reverse=True)


@pytest.mark.parametrize('freq', [220.0, 440.0, 880.0])
def test_mk_wav_freq(freq: float) -> None:
    """指定した周波数の sin波になっている(スペクトルのピークで見る)"""
    wav = Wav(freq, 1.0, RATE).wav

    spectrum = np.abs(np.fft.rfft(wav.astype(np.float64)))
    peak_freq = float(np.fft.rfftfreq(len(wav), 1.0 / RATE)[
        int(np.argmax(spectrum))])

    assert peak_freq == pytest.approx(freq, abs=2.0)


def test_save(tmp_path: Path) -> None:
    """wav形式 で保存できる(モノラル / 16bit)"""
    outfile = tmp_path / 'out.wav'
    wav = Wav(FREQ, SEC, RATE)

    wav.save(outfile)

    with wave.open(str(outfile), 'rb') as w_read:
        assert w_read.getnchannels() == 1
        assert w_read.getsampwidth() == 2
        assert w_read.getframerate() == RATE
        assert w_read.getnframes() == len(wav.wav)

        frames = w_read.readframes(w_read.getnframes())

    assert np.array_equal(
        np.frombuffer(frames, dtype=np.int16), wav.wav)


def test_save_str_path(tmp_path: Path) -> None:
    """出力先は `str` でも `os.PathLike` でも受ける"""
    outfile = tmp_path / 'out.wav'

    Wav(FREQ, SEC, RATE).save(str(outfile))

    assert outfile.exists()


def test_default_params() -> None:
    """既定値でも生成できる"""
    wav = Wav(FREQ).wav

    assert len(wav) == int(Wav.DEF_RATE * Wav.DEF_SEC)

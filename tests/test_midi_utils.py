#
# (c) 2026 Yoichi Tanibayashi
#
"""
`ytmidilib.midi_utils` のテスト
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2026/08'

import pytest

from ytmidilib import FREQ_BASE, NOTE_BASE, NOTE_N, note2freq


def test_note2freq_base() -> None:
    """基準は A4 = note 69 = 440 Hz"""
    assert note2freq(NOTE_BASE) == pytest.approx(FREQ_BASE)


@pytest.mark.parametrize(('note', 'freq'), [
    (NOTE_BASE - 24, 110.0),
    (NOTE_BASE - 12, 220.0),
    (NOTE_BASE + 12, 880.0),
    (NOTE_BASE + 24, 1760.0),
])
def test_note2freq_octave(note: int, freq: float) -> None:
    """1 オクターブ (12 半音) で周波数が 2 倍/半分になる"""
    assert note2freq(note) == pytest.approx(freq)


def test_note2freq_semitone() -> None:
    """隣り合う音の比が 2 の 12 乗根"""
    ratio = 2.0 ** (1.0 / 12.0)

    for note in range(NOTE_BASE - 3, NOTE_BASE + 4):
        assert note2freq(note + 1) / note2freq(note) == pytest.approx(ratio)


def test_note2freq_range() -> None:
    """MIDI ノート番号の両端でも計算でき、単調増加する"""
    freqs = [note2freq(n) for n in range(NOTE_N)]

    assert freqs[0] > 0
    assert freqs[NOTE_N - 1] > freqs[0]
    assert all(f1 < f2 for f1, f2 in zip(freqs, freqs[1:], strict=False))

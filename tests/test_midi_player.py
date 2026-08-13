#
# (c) 2026 Yoichi Tanibayashi
#
"""
`ytmidilib.midi_player` のテスト

**音を鳴らす経路 (`play()` / `mk_wav()`) はテストしない。**
音声デバイスと実時間の `sleep` に依存するため。ここでは、その手前の
計算 (`within_range()` / `snd_key()`) と、再生していないときの状態を見る。
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2026/08'

import pygame
import pytest

from ytmidilib import NoteInfo, Player


@pytest.mark.parametrize(('num', 'expected'), [
    (0.5, 0.5),    # 範囲内
    (0.001, 0.02),  # 下限で止める
    (10.0, 1.2),   # 上限で止める
    (0.02, 0.02),  # 下限ちょうど
    (1.2, 1.2),    # 上限ちょうど
])
def test_within_range(num: float, expected: float) -> None:
    """範囲内に収める"""
    assert Player.within_range(num, Player.SEC_MIN, Player.SEC_MAX) == expected


def test_snd_key_note() -> None:
    """キーの 1 つ目は MIDIノート番号"""
    player = Player()
    key = player.snd_key(NoteInfo(0.0, 0, 60, 100, 0.3))

    assert key[0] == 60


def test_snd_key_clamps_length() -> None:
    """長さは sec_min .. sec_max に収める"""
    player = Player()

    short = player.snd_key(NoteInfo(0.0, 0, 60, 100, 0.001))
    long = player.snd_key(NoteInfo(0.0, 0, 60, 100, 10.0))

    assert short[1] == Player.SEC_MIN
    assert long[1] == Player.SEC_MAX


def test_snd_key_no_end_time() -> None:
    """`end_time` が未設定なら長さ 0 -> 下限に収まる"""
    player = Player()
    key = player.snd_key(NoteInfo(0.0, 0, 60, 100))

    assert key[1] == Player.SEC_MIN


@pytest.mark.parametrize(('length', 'key_sec'), [
    (0.230, 0.23),
    (0.234, 0.23),
    (0.2349, 0.23),  # 0.5 秒以下は 0.01 単位
    (0.600, 0.60),
    (0.601, 0.60),
    (0.610, 0.60),   # 0.5 秒超は 0.02 単位
])
def test_snd_key_round(length: float, key_sec: float) -> None:
    """長さを丸めて、生成する音源の種類数を抑える"""
    player = Player()
    key = player.snd_key(NoteInfo(0.0, 0, 60, 100, length))

    assert key[1] == pytest.approx(key_sec)


def test_snd_key_cache_hit() -> None:
    """わずかに違う長さの音は、同じキーになる(キャッシュが効く)"""
    player = Player()
    keys = {
        player.snd_key(NoteInfo(0.0, 0, 60, 100, length))
        for length in (0.600, 0.601, 0.6049)
    }

    assert len(keys) == 1


def test_snd_key_differs_by_note() -> None:
    """音の高さが違えば別のキー"""
    player = Player()
    key60 = player.snd_key(NoteInfo(0.0, 0, 60, 100, 0.3))
    key64 = player.snd_key(NoteInfo(0.0, 0, 64, 100, 0.3))

    assert key60 != key64


def test_player_is_not_playing() -> None:
    """再生を始めていなければ `is_playing()` は False"""
    assert Player().is_playing() is False


def test_player_stop_without_play() -> None:
    """再生していなくても `stop()` / `close()` を呼べる"""
    player = Player()

    player.stop()
    player.close()

    assert player.is_playing() is False


def test_player_context_manager() -> None:
    """`with` で使うと、抜けるときに `close()` される"""
    with Player() as player:
        assert player.is_playing() is False


def test_player_does_not_init_mixer() -> None:
    """生成しただけでは、音声デバイスを掴まない

    (掴んでいたら、音声デバイスの無い環境でテストが落ちる)
    """
    assert pygame.mixer.get_init() is None

    with Player():
        pass

    assert pygame.mixer.get_init() is None

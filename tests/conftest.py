#
# (c) 2026 Yoichi Tanibayashi
#
"""
pytest の共通 fixture

テスト用の MIDI ファイルは、バイナリを置かずに `mido` で組み立てる
(何をテストしているかがコードから読め、差分も見えるため)。
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2026/08'

from collections import Counter
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import mido
import pytest
from loguru import logger

from ytmidilib import DEF_TICKS_PER_BEAT, DRUM_CHANNEL
from ytmidilib.midi_parser import DEFAULT_TEMPO

MkMidiFile = Callable[..., Path]
"""`mk_midi_file` fixture の型"""

CountMsgTypes = Callable[[mido.MidiFile], dict[str, int]]
"""`count_msg_types` fixture の型"""

LogMessages = list[tuple[str, str]]
"""`log_messages` fixture の型。(水準の名前, メッセージ) の列"""


@pytest.fixture(autouse=True)
def _reset_logger() -> Iterator[None]:
    """loguru のシンクを、テストごとに空にする

    CLI のテストは `mylog.loggerInit()` を通るのでシンクが増える。
    残したままだと、あとのテストのログまで出力されてしまう。
    """
    logger.remove()

    yield

    logger.remove()


@pytest.fixture
def log_messages() -> Iterator[LogMessages]:
    """出力されたログを (水準の名前, メッセージ) で集める

    loguru のログは pytest の `caplog` には入らないので、
    シンクを張って自分で集める。
    """
    msgs: LogMessages = []

    handler_id = logger.add(
        lambda m: msgs.append(
            (m.record['level'].name, m.record['message'])),
        level='DEBUG')

    yield msgs

    logger.remove(handler_id)


@pytest.fixture
def mk_midi_file(tmp_path: Path) -> MkMidiFile:
    """MIDI ファイルを組み立てて保存するファクトリ

    Returns
    -------
    mk: callable
        `mk(tracks, ticks_per_beat=480, name='test.mid', midi_type=1)`
        で保存し、`Path` を返す。`tracks` はメッセージのリストのリスト
    """
    def _mk(tracks: list[list[Any]],
            ticks_per_beat: int = DEF_TICKS_PER_BEAT,
            name: str = 'test.mid',
            midi_type: int = 1) -> Path:
        midi_obj = mido.MidiFile(type=midi_type, ticks_per_beat=ticks_per_beat)

        for msg_list in tracks:
            midi_obj.tracks.append(mido.MidiTrack(msg_list))

        midi_file = tmp_path / name
        midi_obj.save(midi_file)

        return midi_file

    return _mk


@pytest.fixture
def rich_midi_file(mk_midi_file: MkMidiFile) -> Path:
    """メタ情報・音色・テンポ変化・打楽器を含む MIDI

    要求書 2 通目 (#1) の「`note` 以外は変わらない」を確かめるための素材。
    `NoteInfo` が持てない情報 (program_change / control_change /
    track_name / time_signature / トラック構成 / テンポ変化) を
    ひととおり入れてある。

    - type 1 / 2 トラック / ticks_per_beat = 480
    - テンポは途中で 500000 -> 250000 [usec/beat] に変わる
    - ch 0 に 2 音、ch 9 (打楽器) に 1 音
    """
    conductor = [
        mido.MetaMessage('track_name', name='conductor', time=0),
        mido.MetaMessage('time_signature',
                         numerator=3, denominator=4, time=0),
        mido.MetaMessage('set_tempo', tempo=DEFAULT_TEMPO, time=0),
        mido.MetaMessage('set_tempo', tempo=DEFAULT_TEMPO // 2, time=960),
    ]
    piano = [
        mido.MetaMessage('track_name', name='piano', time=0),
        mido.Message('program_change', channel=0, program=42, time=0),
        mido.Message('control_change', channel=0,
                     control=7, value=100, time=0),
        mido.Message('note_on', channel=0, note=60, velocity=100, time=0),
        mido.Message('note_off', channel=0, note=60, velocity=0, time=480),
        mido.Message('note_on', channel=0, note=64, velocity=90, time=0),
        mido.Message('note_off', channel=0, note=64, velocity=0, time=480),
        mido.Message('note_on', channel=DRUM_CHANNEL,
                     note=36, velocity=110, time=0),
        mido.Message('note_off', channel=DRUM_CHANNEL,
                     note=36, velocity=0, time=240),
    ]

    return mk_midi_file([conductor, piano], name='rich.mid')


@pytest.fixture
def count_msg_types() -> CountMsgTypes:
    """MIDI ファイル全体の、メッセージ種別ごとの個数を数える

    Returns
    -------
    count: callable
        `count(midi_obj)` -> `{'note_on': 3, ...}`
    """
    def _count(midi_obj: mido.MidiFile) -> dict[str, int]:
        counter: Counter[str] = Counter()

        for track in midi_obj.tracks:
            for msg in track:
                counter[msg.type] += 1

        return dict(counter)

    return _count

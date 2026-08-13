#
# (c) 2020 Yoichi Tanibayashi
#
"""
midi_tools
"""
from importlib.metadata import PackageNotFoundError, version

from .midi_parser import NoteInfo, ParsedMidi, Parser, VisualData
from .midi_player import Player
from .midi_utils import FREQ_BASE, NOTE_BASE, NOTE_N, note2freq
from .midi_writer import (
    DEF_TICKS_PER_BEAT,
    DRUM_CHANNEL,
    transpose,
    transpose_file,
    write,
)
from .wav_utils import Wav

__author__ = 'Yoichi Tanibayashi'
__date__ = '2020/12'

# バージョンは hatch-vcs が git タグから決めるので、
# インストール済みのメタデータから読む。
# パッケージとして入っていない場合(ソースを直接読んだ場合など)は
# 決めようがないので、それと分かる値を入れておく
__version__: str = '_._._'
if __package__:
    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = '0.0.0'

__all__ = ['__author__', '__date__', '__version__',
           'FREQ_BASE', 'NOTE_BASE', 'NOTE_N', 'note2freq',
           'Parser', 'NoteInfo', 'ParsedMidi', 'VisualData',
           'Player',
           'DEF_TICKS_PER_BEAT', 'DRUM_CHANNEL',
           'write', 'transpose', 'transpose_file',
           'Wav']

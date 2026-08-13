#
# (c) 2020 Yoichi Tanibayashi
#
"""
midi_tools
"""
from importlib.metadata import PackageNotFoundError, version

from .midi_parser import (
    NoteEvent,
    NoteInfo,
    ParsedMidi,
    Parser,
    TimedEvent,
    mk_event_list,
    parse,
)
from .midi_player import Player
from .midi_utils import (
    DEFAULT_TEMPO,
    FREQ_BASE,
    NOTE_BASE,
    NOTE_N,
    note2freq,
)
from .midi_visual import (
    VisualData,
    VisualLine,
    format_visual,
    mk_visual,
    print_visual,
)
from .midi_writer import (
    DEF_TICKS_PER_BEAT,
    DRUM_CHANNEL,
    transpose,
    transpose_file,
    write,
)
from .wav_utils import Wav, init_mixer, quit_mixer

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
           'DEFAULT_TEMPO',
           'FREQ_BASE', 'NOTE_BASE', 'NOTE_N', 'note2freq',
           'Parser', 'parse', 'mk_event_list',
           'NoteInfo', 'ParsedMidi', 'NoteEvent', 'TimedEvent',
           'mk_visual', 'format_visual', 'print_visual',
           'VisualData', 'VisualLine',
           'Player',
           'DEF_TICKS_PER_BEAT', 'DRUM_CHANNEL',
           'write', 'transpose', 'transpose_file',
           'Wav', 'init_mixer', 'quit_mixer']

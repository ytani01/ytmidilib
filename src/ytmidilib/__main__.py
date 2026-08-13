#
# (c) 2020 Yoichi Tanibayashi
#
"""
main for midi_tools
"""
import click
import pygame
from loguru import logger

from . import (
    DRUM_CHANNEL,
    Parser,
    Player,
    Wav,
    __version__,
    mk_visual,
    note2freq,
    print_visual,
    transpose_file,
)
from .click_utils import click_common_opts
from .mylog import loggerInit


class MidiApp:
    """ MIDIファイルをパージングし、必要に応じて可視化/再生する """
    def __init__(self, midi_file: str,
                 channel: tuple[int, ...],
                 parse_only: bool = False,
                 visual_flag: bool = False,
                 rate: int = Player.DEF_RATE,
                 sec_min: float = Player.SEC_MIN,
                 sec_max: float = Player.SEC_MAX,
                 pos_sec: float = 0.0,
                 debug: bool = False) -> None:
        """ Constructor """
        self._dbg = debug
        logger.debug('midi_file={}, channel={}', midi_file, channel)
        logger.debug('parse_only={}, visual_flag={}', parse_only, visual_flag)
        logger.debug('rate={}', rate)
        logger.debug('sec_min/max={}/{}', sec_min, sec_max)
        logger.debug('pos_sec={}', pos_sec)

        self._midi_file = midi_file
        self._channel = channel
        self._parse_only = parse_only
        self._visual_flag = visual_flag
        self._rate = rate
        self._sec_min = sec_min
        self._sec_max = sec_max
        self._pos_sec = pos_sec

        self._parser = Parser(debug=self._dbg)
        self._player = Player(rate=self._rate, debug=self._dbg)

    def main(self) -> None:
        """ main """
        logger.debug('')

        parsed_data = self._parser.parse(self._midi_file, self._channel)

        if self._dbg or self._parse_only:
            for i, data in enumerate(parsed_data['note_info']):
                print(f'({i:4d}) {data}')

        print('channel_set=', parsed_data['channel_set'], flush=True)

        if self._visual_flag:
            v_data = mk_visual(parsed_data['note_info'])
            print()
            print_visual(v_data, parsed_data['channel_set'])

        if self._parse_only:
            return

        self._player.play(parsed_data, self._pos_sec,
                          self._sec_min, self._sec_max)

    def end(self) -> None:
        """ end """
        logger.debug('')

        self._player.close()


class WavApp:
    """ 指定周波数の音源を生成し、再生/保存する """
    def __init__(self,
                 freq: float, outfile: tuple[str, ...],
                 midi_note_flag: bool, vol: float, sec: float,
                 rate: int = Wav.DEF_RATE,
                 play_flag: bool = True,
                 debug: bool = False) -> None:
        """constructor

        Parameters
        ----------
        freq: float
            周波数 [Hz]。midi_note_flag が True の場合は MIDIノート番号
        outfile: tuple of str
            出力ファイル名(空なら保存しない)
        """
        self._dbg = debug
        logger.debug('freq,vol,sec,rate={}', (freq, vol, sec, rate))
        logger.debug('outfile={}', outfile)
        logger.debug('midi_note_flag={}', midi_note_flag)
        logger.debug('play_flag={}', play_flag)

        self._freq = freq
        self._outfile = outfile
        self._vol = vol
        self._sec = sec
        self._rate = rate
        self._play_flag = play_flag

        if midi_note_flag:
            note = int(freq)
            self._freq = note2freq(note)
            print(f'MIDI note: {note} -> freq = {self._freq:.3f} Hz')

    def main(self) -> None:
        """main
        """
        logger.debug('')

        wav = Wav(self._freq, self._sec, self._rate, debug=self._dbg)

        if self._play_flag:
            # 再生するときだけ初期化する(保存だけなら音声デバイス不要)
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self._rate, channels=1)

            wav.play(self._vol)

        if self._outfile:  # not empty (C10801)
            wav.save(self._outfile[0])

        logger.debug('done')

    def end(self) -> None:
        """
        Call at the end of program.
        """
        logger.debug('doing ..')

        if pygame.mixer.get_init():
            pygame.mixer.quit()

        logger.debug('done')


class TransposeApp:
    """ MIDIファイルを移調する """
    def __init__(self, src: str, dst: str, n: int,
                 clip: bool = False, drums: bool = False,
                 debug: bool = False) -> None:
        """ Constructor """
        self._dbg = debug
        logger.debug('src={}, dst={}, n={}', src, dst, n)
        logger.debug('clip={}, drums={}', clip, drums)

        self._src = src
        self._dst = dst
        self._n = n
        self._clip = clip
        self._drums = drums

    def main(self) -> None:
        """ main """
        logger.debug('')

        try:
            transpose_file(self._src, self._dst, self._n,
                           clip=self._clip, drums=self._drums)
        except ValueError as e:
            # 範囲外。--clip で丸められることを案内する
            raise click.ClickException(f'{e} .. use --clip') from e

        print(f'{self._src} -> {self._dst}: {self._n:+d} semitone(s)')

    def end(self) -> None:
        """ end """
        logger.debug('')


# transpose は N に負の値 (-2 など) を取るので、
# オプションと誤解されないように未知のオプションを引数として扱う
TRANSPOSE_CONTEXT_SETTINGS = dict(ignore_unknown_options=True)

# `-v` は既に parse の `--visual`、wav の `--vol` が使っている。
# サブコマンドごとに違うと紛らわしいので、version は
# `-V` / `--version` だけにする (TODO-014)
COMMON_OPTS = click_common_opts(__version__, use_v=False)


@click.group(invoke_without_command=True, help='''
midilib Apps
''')
@COMMON_OPTS
def cli(ctx, debug) -> None:
    """ click group """
    # 出力先の設定は、アプリケーション側であるここで行う。
    # `--debug` は各サブコマンドも持つので、そちらで呼び直す
    loggerInit(debug)

    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@cli.command(help='''
MIDI parser
''')
@click.argument('midi_file', type=click.Path(exists=True))
@click.option('--channel', '-c', 'channel', type=int, multiple=True,
              help='MIDI channel')
@click.option('--visual', '-v', 'visual_flag', is_flag=True,
              default=False,
              help='Visual flag')
@COMMON_OPTS
def parse(ctx, midi_file, channel, visual_flag, debug) -> None:
    """
    parser main
    """
    loggerInit(debug)
    logger.debug('command={!r}', ctx.command.name)

    app = MidiApp(midi_file, channel, parse_only=True,
                  visual_flag=visual_flag,
                  debug=debug)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()


@cli.command(help='''
MIDI player
''')
@click.argument('midi_file', type=click.Path(exists=True))
@click.option('--pos_sec', '-s', 'pos_sec', type=float, default=0,
              help='seek position in sec')
@click.option('--channel', '-c', 'channel', type=int, multiple=True,
              help='MIDI channel')
@click.option('--rate', '-r', 'rate', type=int,
              default=Player.DEF_RATE,
              help=f'sampling rate, default={Player.DEF_RATE} Hz')
@click.option('--sec_min', '--min', 'sec_min', type=float,
              default=Player.SEC_MIN,
              help=f'min sound length, default={Player.SEC_MIN}')
@click.option('--sec_max', '--max', 'sec_max', type=float,
              default=Player.SEC_MAX,
              help=f'max sound length, default={Player.SEC_MAX}')
@COMMON_OPTS
def play(ctx, midi_file, pos_sec, channel, rate, sec_min, sec_max,
         debug) -> None:
    """
    player main
    """
    loggerInit(debug)
    logger.debug('command={!r}', ctx.command.name)

    app = MidiApp(midi_file, channel, parse_only=False,
                  visual_flag=False, rate=rate,
                  sec_min=sec_min, sec_max=sec_max, pos_sec=pos_sec,
                  debug=debug)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()


@cli.command(help='''
Wav format sound tool
''')
@click.argument('freq', type=float)
@click.argument('outfile', type=click.Path(), nargs=-1)
@click.option('--midi_note', '-m', 'midi_note_flag', is_flag=True,
              default=False,
              help='FREQ as MIDI note number')
@click.option('--vol', '-v', 'vol', type=float, default=Wav.DEF_VOL,
              help=f'volume <= {Wav.VOL_MAX}, default={Wav.DEF_VOL}')
@click.option('--sec', '-t', '-s', 'sec', type=float, default=Wav.DEF_SEC,
              help=f'sec [sec], default={Wav.DEF_SEC} sec')
@click.option('--rate', '-r', 'rate', type=int, default=Wav.DEF_RATE,
              help=f'Sampling reate, default={Wav.DEF_RATE} Hz')
@click.option('--dont_play', '-n', 'dont_play', is_flag=True,
              default=False,
              help='dont\'t play flag')
@COMMON_OPTS
def wav(ctx, freq, outfile, midi_note_flag, vol, sec, rate,
        dont_play, debug) -> None:
    """サンプル起動用メイン関数
    """
    loggerInit(debug)
    logger.debug('command={!r}', ctx.command.name)
    logger.debug('freq,vol,sec,rate={}', (freq, vol, sec, rate))
    logger.debug('outfile={}', outfile)
    logger.debug('midi_note_flag={}', midi_note_flag)
    logger.debug('dont_play={}', dont_play)

    app = WavApp(freq, outfile, midi_note_flag, vol, sec, rate,
                 play_flag=not dont_play,
                 debug=debug)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()


@cli.command(context_settings=TRANSPOSE_CONTEXT_SETTINGS, help='''
MIDI transpose: SRC を N 半音(負なら下げる)移調して DST へ書き出す

note 以外は変更しない
''')
@click.argument('src', type=click.Path(exists=True))
@click.argument('dst', type=click.Path())
@click.argument('n', type=int)
@click.option('--clip', '-c', 'clip', is_flag=True, default=False,
              help='clip note into 0..127 (default: error)')
@click.option('--drums', '-D', 'drums', is_flag=True, default=False,
              help=f'transpose channel {DRUM_CHANNEL} (drums), too')
@COMMON_OPTS
def transpose(ctx, src, dst, n, clip, drums, debug) -> None:
    """
    transpose main
    """
    loggerInit(debug)
    logger.debug('command={!r}', ctx.command.name)

    app = TransposeApp(src, dst, n, clip=clip, drums=drums, debug=debug)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()


if __name__ == '__main__':
    cli(prog_name='MidiLib')

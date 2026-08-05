#
# (c) 2020 Yoichi Tanibayashi
#
"""
main for midi_tools
"""
import click
import pygame

from . import Parser, Player, Wav, note2freq
from .my_logger import get_logger, init_handler


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
        self._log = get_logger(self.__class__.__name__, self._dbg)
        self._log.debug('midi_file=%s, channel=%s', midi_file, channel)
        self._log.debug('parse_only=%s, visual_flag=%s',
                        parse_only, visual_flag)
        self._log.debug('rate=%s', rate)
        self._log.debug('sec_min/max=%s/%s', sec_min, sec_max)
        self._log.debug('pos_sec=%s', pos_sec)

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
        self._log.debug('')

        parsed_data = self._parser.parse(self._midi_file, self._channel)

        if self._dbg or self._parse_only:
            for i, data in enumerate(parsed_data['note_info']):
                print(f'({i:4d}) {data}')

        print('channel_set=', parsed_data['channel_set'], flush=True)

        if self._visual_flag:
            v_data = self._parser.mk_visual(parsed_data['note_info'])
            print()
            self._parser.print_visual(v_data, parsed_data['channel_set'])

        if self._parse_only:
            return

        self._player.play(parsed_data, self._pos_sec,
                          self._sec_min, self._sec_max)

    def end(self) -> None:
        """ end """
        self._log.debug('')

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
        self._log = get_logger(self.__class__.__name__, self._dbg)
        self._log.debug('freq,vol,sec,rate=%s', (freq, vol, sec, rate))
        self._log.debug('outfile=%s', outfile)
        self._log.debug('midi_note_flag=%s', midi_note_flag)
        self._log.debug('play_flag=%s', play_flag)

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
        self._log.debug('')

        wav = Wav(self._freq, self._sec, self._rate, debug=self._dbg)

        if self._play_flag:
            # 再生するときだけ初期化する(保存だけなら音声デバイス不要)
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self._rate, channels=1)

            wav.play(self._vol)

        if self._outfile:  # not empty (C10801)
            wav.save(self._outfile[0])

        self._log.debug('done')

    def end(self) -> None:
        """
        Call at the end of program.
        """
        self._log.debug('doing ..')

        if pygame.mixer.get_init():
            pygame.mixer.quit()

        self._log.debug('done')


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(invoke_without_command=True,
             context_settings=CONTEXT_SETTINGS, help='''
midilib Apps
''')
@click.pass_context
def cli(ctx) -> None:
    """ click group """
    # ハンドラの設定は、アプリケーション側であるここで行う
    init_handler()

    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@cli.command(context_settings=CONTEXT_SETTINGS, help='''
MIDI parser
''')
@click.argument('midi_file', type=click.Path(exists=True))
@click.option('--channel', '-c', 'channel', type=int, multiple=True,
              help='MIDI channel')
@click.option('--visual', '-v', 'visual_flag', is_flag=True,
              default=False,
              help='Visual flag')
@click.option('--debug', '-d', 'dbg', is_flag=True, default=False,
              help='debug flag')
def parse(midi_file, channel, visual_flag, dbg) -> None:
    """
    parser main
    """
    log = get_logger(__name__, dbg)

    app = MidiApp(midi_file, channel, parse_only=True,
                  visual_flag=visual_flag,
                  debug=dbg)
    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()


@cli.command(context_settings=CONTEXT_SETTINGS, help='''
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
@click.option('--debug', '-d', 'dbg', is_flag=True, default=False,
              help='debug flag')
def play(midi_file, pos_sec, channel, rate, sec_min, sec_max, dbg) -> None:
    """
    player main
    """
    log = get_logger(__name__, dbg)

    app = MidiApp(midi_file, channel, parse_only=False,
                  visual_flag=False, rate=rate,
                  sec_min=sec_min, sec_max=sec_max, pos_sec=pos_sec,
                  debug=dbg)
    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()


@cli.command(context_settings=CONTEXT_SETTINGS, help='''
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
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def wav(freq, outfile, midi_note_flag, vol, sec, rate,
        dont_play, debug) -> None:
    """サンプル起動用メイン関数
    """
    log = get_logger(__name__, debug)
    log.debug('freq,vol,sec,rate=%s', (freq, vol, sec, rate))
    log.debug('outfile=%s', outfile)
    log.debug('midi_note_flag=%s', midi_note_flag)
    log.debug('dont_play=%s', dont_play)

    app = WavApp(freq, outfile, midi_note_flag, vol, sec, rate,
                 play_flag=not dont_play,
                 debug=debug)
    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()


if __name__ == '__main__':
    cli(prog_name='MidiLib')

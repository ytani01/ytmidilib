#
# (c) 2020 Yoichi Tanibayashi
#
"""
main for midi_tools
"""
import pygame
import click
from . import Parser, Player, Wav, note2freq
from .my_logger import get_logger


class MidiApp:  # pylint: disable=too-many-instance-attributes
    """ MidiApp """
    def __init__(self, midi_file,  # pylint: disable=too-many-arguments
                 channel,
                 parse_only=False,
                 visual_flag=False,
                 rate=Player.DEF_RATE,
                 sec_min=Player.SEC_MIN, sec_max=Player.SEC_MAX,
                 pos_sec=0,
                 debug=False) -> None:
        """ Constructor """
        self._dbg = debug
        self._log = get_logger(self.__class__.__name__, self._dbg)
        self._log.debug('midi_file=%s, channel=%s',
                        midi_file, channel)
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

        self._log.debug('parsed_data=')
        if self._dbg or self._parse_only:
            for i, data in enumerate(parsed_data['note_info']):
                print('(%4d) %s' % (i, data))

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
        """ end

        do nothing
        """


class WavApp:  # pylint: disable=too-many-instance-attributes
    """ WavApp """
    def __init__(self,  # pylint: disable=too-many-arguments
                 freq, outfile, midi_note_flag, vol, sec,
                 rate=Wav.DEF_RATE,
                 play_flag=True,
                 debug=False) -> None:
        """constructor

        Parameters
        ----------
        """
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('freq,vol,sec,rate=%s', (freq, vol, sec, rate))
        self._log.debug('outfile=%s', outfile)
        self._log.debug('midi_note_flag=%s', midi_note_flag)
        self._log.debug('play_flag=%s', play_flag)

        self._freq = freq
        self._outfile = outfile
        self._midi_note_flag = midi_note_flag
        self._vol = vol
        self._sec = sec
        self._rate = rate
        self._play_flag = play_flag

        if self._midi_note_flag:
            note = self._freq
            self._freq = note2freq(note)
            print('MIDI note: %d -> freq = %.3f Hz' % (
                int(note), self._freq))

        pygame.mixer.init(frequency=self._rate, channels=1)

    def main(self):
        """main
        """
        self._log.debug('')

        wav = Wav(self._freq,  # pylint: disable=redefined-outer-name
                  self._sec, self._rate,
                  debug=self._dbg)

        if self._play_flag:
            wav.play(self._vol)

        if self._outfile:  # not empty (C10801)
            wav.save(self._outfile[0])

        self._log.debug('done')

    def end(self):
        """
        Call at the end of program.
        """
        self._log.debug('doing ..')
        self._log.debug('done')


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(invoke_without_command=True,
             context_settings=CONTEXT_SETTINGS, help='''
midilib Apps
''')
@click.pass_context
def cli(ctx):
    """ click group """
    subcmd = ctx.invoked_subcommand

    if subcmd is None:
        print(ctx.get_help())
    else:
        pass


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
              help='sampling rate, default=%s Hz' % Player.DEF_RATE)
@click.option('--sec_min', '--min', 'sec_min', type=float,
              default=Player.SEC_MIN,
              help='min sound length, default=%s' % (Player.SEC_MIN))
@click.option('--sec_max', '--max', 'sec_max', type=float,
              default=Player.SEC_MAX,
              help='max sound length, default=%s' % (Player.SEC_MAX))
@click.option('--debug', '-d', 'dbg', is_flag=True, default=False,
              help='debug flag')
def play(midi_file,  # pylint: disable=too-many-arguments
         pos_sec, channel, rate, sec_min, sec_max, dbg) -> None:
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
              help='volume <= %s, default=%s' % (
                  Wav.VOL_MAX, Wav.DEF_VOL))
@click.option('--sec', '-t', '-s', 'sec', type=float, default=Wav.DEF_SEC,
              help='sec [sec], default=%s sec' % Wav.DEF_SEC)
@click.option('--rate', '-r', 'rate', type=int, default=Wav.DEF_RATE,
              help='Sampling reate, default=%s Hz' % Wav.DEF_RATE)
@click.option('--dont_play', '-n', 'dont_play', is_flag=True,
              default=False,
              help='dont\'t play flag')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def wav(freq, outfile,  # pylint: disable=too-many-arguments
        midi_note_flag,
        vol, sec, rate,
        dont_play,
        debug):
    """サンプル起動用メイン関数
    """
    _log = get_logger(__name__, debug)
    _log.debug('freq,vol,sec,rate=%s', (freq, vol, sec, rate))
    _log.debug('outfile=%s', outfile)
    _log.debug('midi_note_flag=%s', midi_note_flag)
    _log.debug('dont_play=%s', dont_play)

    app = WavApp(freq, outfile, midi_note_flag, vol, sec, rate,
                 play_flag=not dont_play,
                 debug=debug)
    try:
        app.main()
    finally:
        _log.debug('finally')
        app.end()


if __name__ == '__main__':
    cli(prog_name='MidiLib')

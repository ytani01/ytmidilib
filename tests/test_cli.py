#
# (c) 2026 Yoichi Tanibayashi
#
"""
CLI (`ytmidilib.__main__`) のテスト

`CliRunner` で呼ぶ(サブプロセスを起動しない)。**音を鳴らすサブコマンド
(`play`) はテストしない。** `wav` は `-n` (再生しない) を付けて、
音声デバイスを掴まない経路だけを通す。
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2026/08'

from pathlib import Path

import mido
import pytest
from click.testing import CliRunner

from ytmidilib import DRUM_CHANNEL, __version__
from ytmidilib.__main__ import cli


@pytest.fixture
def runner() -> CliRunner:
    """click のテストランナー"""
    return CliRunner()


def _notes(midi_file: Path, channel: int) -> list[int]:
    """指定チャンネルの note_on の note を並べる"""
    midi_obj = mido.MidiFile(midi_file)

    return [msg.note for track in midi_obj.tracks for msg in track
            if msg.type == 'note_on' and msg.channel == channel]


# --- group ----------------------------------------------------------

def test_cli_no_args(runner: CliRunner) -> None:
    """引数なしならヘルプを出す(エラーにはしない)"""
    result = runner.invoke(cli, [])

    assert result.exit_code == 0
    assert 'Usage:' in result.stdout


def test_cli_help(runner: CliRunner) -> None:
    """`-h` に全サブコマンドが並ぶ"""
    result = runner.invoke(cli, ['-h'])

    assert result.exit_code == 0
    for subcmd in ('parse', 'play', 'wav', 'transpose'):
        assert subcmd in result.stdout


# --- 共通オプション --------------------------------------------------

@pytest.mark.parametrize('args', [
    ['-V'], ['--version'],
    ['parse', '-V'], ['play', '-V'], ['wav', '-V'],
    # transpose は ignore_unknown_options だが、-V は既知なので効く
    ['transpose', '-V'],
])
def test_version(runner: CliRunner, args: list[str]) -> None:
    """`-V` / `--version` はどのコマンドでも効く"""
    result = runner.invoke(cli, args)

    assert result.exit_code == 0
    assert __version__ in result.stdout


# --- parse ----------------------------------------------------------

def test_parse(runner: CliRunner, rich_midi_file: Path) -> None:
    """パージング結果と channel_set を出す"""
    result = runner.invoke(cli, ['parse', str(rich_midi_file)])

    assert result.exit_code == 0
    assert 'channel_set=' in result.stdout
    assert 'note:060' in result.stdout
    assert f'channel:{DRUM_CHANNEL:02d}' in result.stdout


def test_parse_visual(runner: CliRunner, rich_midi_file: Path) -> None:
    """`-v` で可視化を出す"""
    result = runner.invoke(cli, ['parse', '-v', str(rich_midi_file)])

    assert result.exit_code == 0
    assert 'CH( 0): A--a' in result.stdout
    assert f'CH( {DRUM_CHANNEL}): J--j' in result.stdout


def test_parse_channel(runner: CliRunner, rich_midi_file: Path) -> None:
    """`-c` で絞り込む。channel_set は元ファイルのまま"""
    result = runner.invoke(cli, ['parse', '-c', '0', str(rich_midi_file)])

    assert result.exit_code == 0
    assert 'channel:00' in result.stdout
    assert f'channel:{DRUM_CHANNEL:02d}' not in result.stdout
    # 絞り込んでも、元ファイルに ch 9 があったことは分かる
    assert str(DRUM_CHANNEL) in result.stdout.split('channel_set=')[1]


def test_parse_no_such_file(runner: CliRunner, tmp_path: Path) -> None:
    """存在しないファイルは click が弾く"""
    result = runner.invoke(cli, ['parse', str(tmp_path / 'nosuch.mid')])

    assert result.exit_code == 2
    assert 'does not exist' in result.stderr


# --- transpose ------------------------------------------------------

def test_transpose(runner: CliRunner, rich_midi_file: Path,
                   tmp_path: Path) -> None:
    """移調できる"""
    dst = tmp_path / 'out.mid'

    result = runner.invoke(
        cli, ['transpose', str(rich_midi_file), str(dst), '2'])

    assert result.exit_code == 0
    assert '+2 semitone(s)' in result.stdout
    assert _notes(dst, 0) == [62, 66]


def test_transpose_negative(runner: CliRunner, rich_midi_file: Path,
                            tmp_path: Path) -> None:
    """負の値がオプションと誤解されない"""
    dst = tmp_path / 'out.mid'

    result = runner.invoke(
        cli, ['transpose', str(rich_midi_file), str(dst), '-2'])

    assert result.exit_code == 0
    assert '-2 semitone(s)' in result.stdout
    assert _notes(dst, 0) == [58, 62]


def test_transpose_drums(runner: CliRunner, rich_midi_file: Path,
                         tmp_path: Path) -> None:
    """`-D` で打楽器チャンネルもずらす"""
    dst_keep = tmp_path / 'keep.mid'
    dst_shift = tmp_path / 'shift.mid'

    runner.invoke(cli, ['transpose', str(rich_midi_file), str(dst_keep), '2'])
    result = runner.invoke(
        cli, ['transpose', '-D', str(rich_midi_file), str(dst_shift), '2'])

    assert result.exit_code == 0
    assert _notes(dst_keep, DRUM_CHANNEL) == [36]
    assert _notes(dst_shift, DRUM_CHANNEL) == [38]


def test_transpose_out_of_range(runner: CliRunner, rich_midi_file: Path,
                                tmp_path: Path) -> None:
    """範囲外は 1 行のエラーにする(トレースバックを出さない)"""
    dst = tmp_path / 'out.mid'

    result = runner.invoke(
        cli, ['transpose', str(rich_midi_file), str(dst), '100'])

    assert result.exit_code == 1
    assert 'Error: note out of range' in result.stderr
    assert 'use --clip' in result.stderr
    assert 'Traceback' not in result.output
    assert not dst.exists()


def test_transpose_clip(runner: CliRunner, rich_midi_file: Path,
                        tmp_path: Path) -> None:
    """`--clip` を付ければ丸めて通る"""
    dst = tmp_path / 'out.mid'

    result = runner.invoke(
        cli, ['transpose', '--clip', str(rich_midi_file), str(dst), '100'])

    assert result.exit_code == 0
    assert _notes(dst, 0) == [127, 127]


def test_transpose_help(runner: CliRunner) -> None:
    """ヘルプの体裁(`-h` が効き、オプションが並ぶ)"""
    result = runner.invoke(cli, ['transpose', '-h'])

    assert result.exit_code == 0
    assert 'SRC' in result.stdout
    assert '--clip' in result.stdout
    assert '--drums' in result.stdout


# --- wav ------------------------------------------------------------

def test_wav_save(runner: CliRunner, tmp_path: Path) -> None:
    """`-n` なら、再生せずに保存だけする(音声デバイス不要)"""
    outfile = tmp_path / 'out.wav'

    result = runner.invoke(
        cli, ['wav', '-n', '-t', '0.1', '-r', '8000', '440', str(outfile)])

    assert result.exit_code == 0
    assert outfile.exists()


def test_wav_vol(runner: CliRunner, tmp_path: Path) -> None:
    """`-v` は version ではなく音量(`--vol`)のまま(TODO-014)"""
    outfile = tmp_path / 'out.wav'

    result = runner.invoke(
        cli, ['wav', '-n', '-v', '0.5', '-t', '0.1', '-r', '8000',
              '440', str(outfile)])

    assert result.exit_code == 0
    assert outfile.exists()


def test_wav_midi_note(runner: CliRunner, tmp_path: Path) -> None:
    """`-m` で FREQ を MIDIノート番号として扱う"""
    outfile = tmp_path / 'out.wav'

    result = runner.invoke(
        cli, ['wav', '-n', '-m', '-t', '0.1', '-r', '8000',
              '69', str(outfile)])

    assert result.exit_code == 0
    assert 'MIDI note: 69 -> freq = 440.000 Hz' in result.stdout

#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
MIDI parser
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2021/01'

import copy
import mido  # pylint: disable=import-error
from .my_logger import get_logger


class NoteInfo:
    """
    parsed MIDI data entity

    Attributes
    ----------
    abs_time: float
        sec >= 0
    channel: int
        0 .. 15
    note: int
        0 .. 127
    velocity: int
        0 .. 127
    end_time: float
        sec >= abs_time >= 0
    """
    def __init__(self,  # pylint: disable=too-many-arguments
                 abs_time=None, channel=None, note=None,
                 velocity=None, end_time=None, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)

        self.abs_time = round(abs_time, 3)
        self.channel = channel
        self.note = note
        self.velocity = velocity
        self.end_time = None
        if isinstance(end_time, float):
            self.end_time = round(end_time, 3)

    def __str__(self):
        """
        Returns
        -------
        str_data: str

        """
        str_data = 'start:%08.3f channel:%02d note:%03d velocity:%03d' % (
            self.abs_time, self.channel, self.note, self.velocity)

        if self.end_time and isinstance(self.end_time, float):
            str_data += ' end:%08.3f length:%05.2f' % (
                self.end_time, self.length())

        return str_data

    def length(self):
        """
        Returns
        -------
        length: float
            length of note [msec]
        """
        return self.end_time - self.abs_time


class Parser:
    """
    MIDI parser
    """
    MIDI_NOTE_N = 128

    V_CHR_ON = '|'
    V_CHR_OFF = ' '

    V_CHR_START = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    V_CHR_STOP = 'abcdefghijklmnopqrstuvwxyz'

    def __init__(self, debug=False):
        """ Constructor

        Parameters
        ----------
        midi_file: str
            file name of MIDI file
        """
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)

        self._channel_set = None

    def parse1(self, midi_obj, channel=None):
        """
        parse MIDI format simply for subsequent parsing step

        Parameters
        ----------
        midi_obj:
            MIDI file obj
        channel: list of int
            selected channel

        Returns
        -------
        data: list of NoteInfo

        """
        # self._log.debug('midi_obj=%s', midi_obj.__dict__)
        # self._log.debug('channel=%s', channel)

        merged_tracks = mido.merge_tracks(midi_obj.tracks)

        tpb = midi_obj.ticks_per_beat

        channel_set = set()
        out_data = []
        abs_time = 0
        cur_tempo = None

        for msg in merged_tracks:
            delta_sec = 0
            try:
                if cur_tempo:
                    delta_sec = mido.tick2second(msg.time, tpb, cur_tempo)
            except KeyError:
                pass

            abs_time += delta_sec

            if msg.type == 'set_tempo':
                cur_tempo = msg.tempo
                continue

            if msg.type == 'end_of_track':
                self._log.debug(msg.__dict__)
                break

            if msg.type == 'note_off':
                channel_set.add(msg.channel)
                if channel and msg.channel not in channel:
                    continue

                data_ent = NoteInfo(abs_time, msg.channel, msg.note, 0,
                                    debug=self._dbg)

                out_data.append(data_ent)

            if msg.type == 'note_on':
                channel_set.add(msg.channel)
                if channel and msg.channel not in channel:
                    continue

                data_ent = NoteInfo(abs_time, msg.channel, msg.note,
                                    msg.velocity, debug=self._dbg)
                out_data.append(data_ent)

        return (channel_set, out_data)

    def set_end_time(self, in_data):
        """
        set end time of NoteInfo
        """
        self._log.debug('')

        out_data = copy.deepcopy(in_data)
        note_start = {}

        ent = None
        for i, ent in enumerate(out_data):
            key = (ent.channel, ent.note)

            if ent.velocity > 0:
                if key in note_start.keys():
                    note_start[key].append(i)
                else:
                    note_start[key] = [i]

                # self._log.debug('note_start=%s', note_start)
                continue

            # velocity == 0

            ent.end_time = ent.abs_time

            try:
                idx2 = note_start[key].pop(0)
            except KeyError as ex:
                msg = '%s:%s .. ignored' % (type(ex).__name__, ex)
                self._log.warning(msg)
                continue

            # self._log.debug('%s, %s, %s', key, note_start[key], idx2)

            out_data[idx2].end_time = ent.abs_time

            if not note_start[key]:
                note_start.pop(key)

            # self._log.debug('note_start=%s', note_start)

        for k in note_start:
            for idx in note_start[k]:
                if ent:
                    out_data[idx].end_time = ent.abs_time

        # self._log.debug('note_start=%s', note_start)

        return out_data

    def parse(self, midi_file, channel=None):
        """
        parse MIDI data

        Parameters
        ----------
        midi_file: str
            MIDI file name
        channel: list of int or None for all channels
            MIDI channel

        Returns
        -------
        out_data: {
            'channel_set': set of int,
            'note_info': list of NoteInfo
        }

        """
        self._log.debug('midi_file=%s, channel=%s', midi_file, channel)

        midi_obj = mido.MidiFile(midi_file)

        self._channel_set, data1 = self.parse1(midi_obj, channel)

        self._log.debug('channel_set=%s', self._channel_set)

        data2 = self.set_end_time(data1)

        # remove velocity == 0
        data3 = []
        for d in data2:
            if d.velocity > 0:
                data3.append(d)

        out_data = {
            'channel_set': self._channel_set,
            'note_info': data3
        }
        return out_data

    def mk_event_list(self, data):
        """
        Parameters
        ----------
        data: list of NoteInfo

        Returns
        -------
        sorted_ev: list of NoteEvent
        """
        ev = []

        for i, ni in enumerate(data):
            if ni.velocity == 0:
                continue

            ev.append({
                'abs_time': ni.abs_time,
                'event': [{'note': ni.note,
                           'channel': ni.channel,
                           'velocity': ni.velocity}]
            })
            ev.append({
                'abs_time': ni.end_time,
                'event': [{'note': ni.note,
                           'channel': ni.channel,
                           'velocity': 0}]
            })

        sorted_ev = sorted(ev, key=lambda x: x['abs_time'])

        merged_ev = []
        abs_time = -1
        for ev in sorted_ev:
            if ev['abs_time'] != abs_time:
                merged_ev.append(ev)
                abs_time = ev['abs_time']
                continue

            merge_flag = False
            for e1 in merged_ev[-1]['event']:
                if e1['note'] == ev['event'][0]['note']:
                    merge_flag = True
                    break

            if merge_flag:
                merged_ev.append(ev)
                continue

            merged_ev[-1]['event'].append(ev['event'][0])

        return merged_ev

    def mk_visual(self, data):
        """
        Parameters
        ----------
        data: list of NoteInfo
        """
        ev = self.mk_event_list(data)

        note_min = self.MIDI_NOTE_N - 1
        note_max = 0

        v_data = []
        prev_chr_list = [self.V_CHR_OFF] * self.MIDI_NOTE_N
        on_count = [0] * self.MIDI_NOTE_N

        for e in ev:
            v_data.append({'abs_time': e['abs_time'],
                           'chr': copy.deepcopy(prev_chr_list)})

            for e1 in e['event']:
                note = e1['note']

                note_min = min(note, note_min)
                note_max = max(note, note_max)

                if e1['velocity'] > 0:
                    ch1 = self.V_CHR_START[e1['channel']]
                    on_count[note] += 1
                    ch2 = self.V_CHR_ON
                else:
                    ch1 = self.V_CHR_STOP[e1['channel']]
                    on_count[note] -= 1
                    if on_count[note] > 0:
                        ch2 = self.V_CHR_ON
                    else:
                        ch2 = self.V_CHR_OFF

                v_data[-1]['chr'][note] = ch1
                prev_chr_list[note] = ch2

        self._log.debug('note_min/max=%s', (note_min, note_max))

        for v_ent in v_data:
            v_ent['chr'] = ''.join(v_ent['chr'][note_min:note_max+1])

        out_data = {
            'note_min': note_min,
            'note_max': note_max,
            'data': v_data
        }
        return out_data

    def print_visual(self, v_data, channel_set):
        """
        Parameters
        ----------
        v_data: {abs_time: v_str}
        channel_set: set of int
        """
        self._log.debug('note_min/max=%s', (
            v_data['note_min'], v_data['note_max']))
        self._log.debug('channel_set=%s', channel_set)

        note_min = v_data['note_min']
        note_max = v_data['note_max']

        for i in [0, 1, 2]:
            print('%8s|' % ' ', end='')
            for n in range(note_min, note_max+1):
                print(('%03d' % (n))[i], end='')

            print('|')

        print('--------+' + '-' * (note_max - note_min + 1) + '+')

        for v_ent in v_data['data']:
            print('%08.3f|%s|' % (v_ent['abs_time'], v_ent['chr']))

        print('--------+' + '-' * (note_max - note_min + 1) + '+')

        for i in [0, 1, 2]:
            print('%8s|' % ' ', end='')
            for n in range(note_min, note_max+1):
                print(('%03d' % (n))[i], end='')

            print('|')

        print()

        for c in sorted(list(channel_set)):
            print('CH(%2d): %s--%s' % (
                c, self.V_CHR_START[c], self.V_CHR_STOP[c]))

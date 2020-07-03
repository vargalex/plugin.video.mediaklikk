# -*- coding: utf-8 -*-

# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import datetime
import itertools
import re
from itertools import izip

ATTRIBUTELISTPATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')


class ParseError(Exception):

    def __init__(self, lineno, line):
        self.lineno = lineno
        self.line = line

    def __str__(self):
        return 'Syntax error in manifest on line %d: %s' % (self.lineno, self.line)


def parse(content, strict=False):
    '''
    Given a M3U8 playlist content returns a dictionary with all data found
    '''
    data = {
        'media_sequence': 0,
        'is_variant': False,
        'is_endlist': False,
        'is_i_frames_only': False,
        'is_independent_segments': False,
        'playlist_type': None,
        'playlists': [],
        'segments': [],
        'iframe_playlists': [],
        'media': [],
        'keys': []
    }

    state = {
        'expect_segment': False,
        'expect_playlist': False,
        'current_key': None,
    }

    lineno = 0
    for line in string_to_lines(content):
        lineno += 1
        line = line.strip()

        if line.startswith('#EXT-X-STREAM-INF'):
            state['expect_playlist'] = True
            _parse_stream_inf(line, data, state)

        # Comments and whitespace
        elif line.startswith('#'):
            # comment
            pass

        elif line.strip() == '':
            # blank lines are legal
            pass

        elif state['expect_segment']:
            _parse_ts_chunk(line, data, state)
            state['expect_segment'] = False

        elif state['expect_playlist']:
            _parse_variant_playlist(line, data, state)
            state['expect_playlist'] = False

        elif strict:
            raise ParseError(lineno, line)

    return data


def _parse_ts_chunk(line, data, state):
    segment = state.pop('segment')
    if state.get('current_program_date_time'):
        segment['program_date_time'] = state['current_program_date_time']
        state['current_program_date_time'] += datetime.timedelta(seconds=segment['duration'])
    segment['uri'] = line
    segment['cue_out'] = state.pop('cue_out', False)
    if state.get('current_cue_out_scte35'):
        segment['scte35'] = state['current_cue_out_scte35']
        segment['scte35_duration'] = state['current_cue_out_duration']
    segment['discontinuity'] = state.pop('discontinuity', False)
    if state.get('current_key'):
        segment['key'] = state['current_key']
    else:
        # For unencrypted segments, the initial key would be None
        if None not in data['keys']:
            data['keys'].append(None)
    data['segments'].append(segment)


def _parse_attribute_list(prefix, line, atribute_parser):
    params = ATTRIBUTELISTPATTERN.split(line.replace(prefix + ':', ''))[1::2]

    attributes = {}
    for param in params:
        name, value = param.split('=', 1)
        name = normalize_attribute(name)

        if name in atribute_parser:
            value = atribute_parser[name](value)

        attributes[name] = value

    return attributes


def _parse_stream_inf(line, data, state):
    data['is_variant'] = True
    data['media_sequence'] = None
    atribute_parser = remove_quotes_parser('codecs', 'audio', 'video', 'subtitles')
    atribute_parser["program_id"] = int
    atribute_parser["bandwidth"] = lambda x: int(float(x))
    atribute_parser["average_bandwidth"] = int
    state['stream_info'] = _parse_attribute_list('#EXT-X-STREAM-INF', line, atribute_parser)


def _parse_variant_playlist(line, data, state):
    playlist = {'uri': line,
                'stream_info': state.pop('stream_info')}

    data['playlists'].append(playlist)


def string_to_lines(string):
    return string.strip().replace('\r\n', '\n').split('\n')


def remove_quotes_parser(*attrs):
    return dict(list(izip(attrs, itertools.repeat(remove_quotes))))


def remove_quotes(string):
    '''
    Remove quotes from string.

    Ex.:
      "foo" -> foo
      'foo' -> foo
      'foo  -> 'foo

    '''
    quotes = ('"', "'")
    if string and string[0] in quotes and string[-1] in quotes:
        return string[1:-1]
    return string


def normalize_attribute(attribute):
    return attribute.replace('-', '_').lower().strip()

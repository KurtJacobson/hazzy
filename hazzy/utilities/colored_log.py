#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson

#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:

#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.

#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import re
import time
from copy import copy
from logging import Formatter

MAPPING = {
    'DEBUG': 'white',
    'INFO': 'cyan',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bgred',
}

PREFIX = '\033['
SUFFIX = '\033[0m'

COLORS = {
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37,
    'bgred': 41,
    'bggrey': 100
    }

# Matches just the first color<text>
# ^(.*?)<([^)]+)> 

# Matches all color<text>
# ([^<\s]+)<([^>]+)>
# (\w+)<([^>]+)>

parse = re.compile(r'(\w+)<([^>]+)>')

class ColoredFormatter(Formatter):

    def __init__(self, patern):
        Formatter.__init__(self, patern)

    def colorer(self, text, color=None):
        if color not in COLORS:
            color = 'white'
        clr = COLORS[color]
        return (PREFIX + '%dm%s' + SUFFIX) % (clr, text)


    def text_colorer(self, raw_msg):
        # Example: red<Testing> will be rendered as red in terminal
        plain_msg = color_msg = raw_msg
#        start = time.time()
        if '<' in raw_msg:
            iterater = parse.finditer(raw_msg)
#            print time.time() - start
            if iterater:
                for match in iterater:
                    raw_word = match.group()
                    color_name = match.group(1)
                    text = match.group(2)

                    color_msg = color_msg.replace(raw_word, self.colorer(text, color_name))
                    plain_msg = plain_msg.replace(raw_word, text)

#        print time.time() - start
        return plain_msg, color_msg

#        start = time.time()
#        words = raw_msg.split(' ')
#        clr_msg = []
#        for word in words:
#            if '$' in word:
#                ind = word.index('$')
#                clr = word[:ind]
#                text = word[ind+1:]
#                word = self.colorer(text, clr)
#            clr_msg.append(word)
#        msg = ' '.join(clr_msg)
#        print time.time() - start
#        return msg, msg

    def format(self, record):
        colored_record = copy(record)

        # Add colors to levelname
        levelname = colored_record.levelname
        color = MAPPING.get(levelname, 'white')
        colored_levelname = self.colorer(levelname, color)
        colored_record.levelname = colored_levelname

        # Add colors to message text
        msg = colored_record.getMessage()
        plain_msg, color_msg = self.text_colorer(msg)
        record.msg = plain_msg
        colored_record.msg = color_msg

        return Formatter.format(self, colored_record)


# ********* Example Usage *********

if __name__ == '__main__':

    import logging

    # Create logger
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    # Add console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    cf = ColoredFormatter("[%(name)s][%(levelname)s]  %(message)s (%(filename)s:%(lineno)d)")
    ch.setFormatter(cf)
    log.addHandler(ch)

    # Add file handler
    fh = logging.FileHandler('hazzy.log')
    fh.setLevel(logging.DEBUG)
    ff = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(ff)
    log.addHandler(fh)

    log.debug('Spindle has been green$STARTED')
    log.info('Spindle has been red$STOPED')
    log.warning('warning')
    log.error('error')
    log.critical('critical')

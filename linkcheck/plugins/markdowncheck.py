# -*- coding: utf-8 -*-
#
# Copyright © 2014 Vadym Khokhlov
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Parse links in Markdown files.

Supported links are:
        <http://autolink.com>
        [name](http://link.com "Optional title")
        [id]: http://link.com "Optional title"
"""

# Some ideas and code were borrowed from https://pypi.python.org/pypi/markdown2 project

import re

from . import _ContentPlugin
from .. import log, LOG_PLUGIN


class MarkdownCheck(_ContentPlugin):
    """Markdown parsing plugin."""

    _filename_re_key = "filename_re"
    _default_filename_re = re.compile(r'.*\.(markdown|md(own)?|mkdn?)$')

    _link_res = [re.compile(r'<((https?|ftp):[^\'">\s]+)>', re.I),
                 re.compile(r"""
                    \[.+\]: # id
                    [ \t]*\n?               # maybe *one* newline
                    [ \t]*
                    <?(.+?)>?           # url = \1
                    [ \t]*
                    (?:
                    \n?             # maybe one newline
                    [ \t]*
                    (?<=\s)         # lookbehind for whitespace
                    ['"(]
                    [^\n]*          # title
                    ['")]
                    [ \t]*
                    )?  # title is optional
                    (?:\n+|\Z)
                    """, re.X | re.M | re.U)]

    _whitespace = re.compile(r'\s*')

    _strip_anglebrackets = re.compile(r'<(.*)>.*')

    _inline_link_title = re.compile(r'''
            (                   # \1
              [ \t]+
              (['"])            # quote char
              (.*?)
            )?                  # title is optional
          \)$
        ''', re.X | re.S)

    def __init__(self, config):
        super(MarkdownCheck, self).__init__(config)
        self.filename_re = self._default_filename_re
        pattern = config.get(self._filename_re_key)
        if pattern:
            try:
                self.filename_re = re.compile(pattern)
            except re.error as msg:
                log.warn(LOG_PLUGIN, "Invalid regex pattern %r: %s" % (pattern, msg))

    @classmethod
    def read_config(cls, configparser):
        """Read configuration file options."""
        config = dict()
        config[cls._filename_re_key] = configparser.get(cls.__name__, cls._filename_re_key) \
            if configparser.has_option(cls.__name__, cls._filename_re_key) else None
        return config

    def applies_to(self, url_data, pagetype=None):
        """Check for Markdown file."""
        return self.filename_re.search(url_data.base_url) is not None

    def check(self, url_data):
        """Extracts urls from the file."""
        content = url_data.get_content()
        self._check_by_re(url_data, content)
        self._check_inline_links(url_data, content)

    def _save_url(self, url_data, content, url_text, url_pos):
        """Saves url. Converts url to 1-line text and url position as offset from the file beginning to (line, column).

        :param url_data: object for url storing
        :param content: file content
        :param url_text: url text
        :param url_pos: url position from the beginning
        """
        line = content.count('\n', 0, url_pos) + 1
        column = url_pos - content.rfind('\n', 0, url_pos)
        url_data.add_url(url_text.translate(None, '\n '), line=line, column=column)

    def _check_by_re(self, url_data, content):
        """ Finds urls by re.

        :param url_data: object for url storing
        :param content: file content
        """
        for link_re in self._link_res:
            for u in link_re.finditer(content):
                self._save_url(url_data, content, u.group(1), u.start(1))

    def _find_balanced(self, text, start, open_c, close_c):
        """Returns the index where the open_c and close_c characters balance
        out - the same number of open_c and close_c are encountered - or the
        end of string if it's reached before the balance point is found.
        """
        i = start
        l = len(text)
        count = 1
        while count > 0 and i < l:
            if text[i] == open_c:
                count += 1
            elif text[i] == close_c:
                count -= 1
            i += 1
        return i

    def _extract_url_and_title(self, text, start):
        """Extracts the url from the tail of a link."""
        # text[start] equals the opening parenthesis
        idx = self._whitespace.match(text, start + 1).end()
        if idx == len(text):
            return None, None
        end_idx = idx
        has_anglebrackets = text[idx] == "<"
        if has_anglebrackets:
            end_idx = self._find_balanced(text, end_idx+1, "<", ">")
        end_idx = self._find_balanced(text, end_idx, "(", ")")
        match = self._inline_link_title.search(text, idx, end_idx)
        if not match:
            return None, None
        url = text[idx:match.start()]
        if has_anglebrackets:
            url = self._strip_anglebrackets.sub(r'\1', url)
        return url, end_idx

    def _check_inline_links(self, url_data, content):
        """Checks inline links.

        :param url_data: url_data object
        :param content: content for processing
        """
        MAX_LINK_TEXT_SENTINEL = 3000
        curr_pos = 0
        content_length = len(content)
        while True:  # Handle the next link.
            # The next '[' is the start of:
            # - an inline anchor:   [text](url "title")
            # - an inline img:      ![text](url "title")
            # - not markup:         [...anything else...
            try:
                start_idx = content.index('[', curr_pos)
            except ValueError:
                break

            # Find the matching closing ']'.
            bracket_depth = 0
            for p in range(start_idx+1, min(start_idx+MAX_LINK_TEXT_SENTINEL, content_length)):
                if content[p] == ']':
                    bracket_depth -= 1
                    if bracket_depth < 0:
                        break
                elif content[p] == '[':
                    bracket_depth += 1
            else:
                # Closing bracket not found within sentinel length. This isn't markup.
                curr_pos = start_idx + 1
                continue

            # Now determine what this is by the remainder.
            p += 1
            if p >= content_length:
                return

            if content[p] == '(':
                url, url_end_idx = self._extract_url_and_title(content, p)
                if url is not None:
                    self._save_url(url_data, content, url, p)
                    start_idx = url_end_idx

            # Otherwise, it isn't markup.
            curr_pos = start_idx + 1

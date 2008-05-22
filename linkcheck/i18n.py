# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
Application internationalization support.
"""

# i18n suppport
import os
import locale
import gettext

# more supported languages are added in init()
supported_languages = set(['en'])
default_language = 'en'
default_encoding = locale.getpreferredencoding()
# It can happen that the preferrec encoding is not determinable, which
# means the function returned None. Fall back to ASCII in this case.
if default_encoding is None:
    default_encoding = "ascii"

def install_builtin (translator, do_unicode):
    """Install _() and _n() gettext methods into default namespace."""
    import __builtin__
    if do_unicode:
        __builtin__.__dict__['_'] = translator.ugettext
        # also install ngettext
        __builtin__.__dict__['_n'] = translator.ungettext
    else:
        __builtin__.__dict__['_'] = translator.gettext
        # also install ngettext
        __builtin__.__dict__['_n'] = translator.ngettext

class Translator (gettext.GNUTranslations):
    """A translation class always installing its gettext methods into the
    default namespace."""

    def install (self, do_unicode):
        """Install gettext methods into the default namespace."""
        install_builtin(self, do_unicode)


class NullTranslator (gettext.NullTranslations):
    """A dummy translation class always installing its gettext methods into
    the default namespace."""

    def install (self, do_unicode):
        """Install gettext methods into the default namespace."""
        install_builtin(self, do_unicode)


def init (domain, directory):
    """Initialize this gettext i18n module. Searches for supported languages
    and installs the gettext translator class."""
    global default_language, default_encoding
    if os.path.isdir(directory):
        # get supported languages
        for lang in os.listdir(directory):
            path = os.path.join(directory, lang, 'LC_MESSAGES')
            if os.path.exists(os.path.join(path, '%s.mo' % domain)):
                supported_languages.add(lang)
    loc, encoding = get_locale()
    if loc in supported_languages:
        default_language = loc
        default_encoding = encoding
    # install translation service routines into default namespace
    translator = get_translator(domain, directory,
                                languages=[default_language], fallback=True)
    do_unicode = True
    translator.install(do_unicode)


def get_translator (domain, directory, languages=None,
                    translatorklass=Translator, fallback=False,
                    fallbackklass=NullTranslator):
    """Search the appropriate GNUTranslations class."""
    translator = gettext.translation(domain, localedir=directory,
            languages=languages, class_=translatorklass, fallback=fallback)
    if not isinstance(translator, gettext.GNUTranslations) and fallbackklass:
        translator = fallbackklass()
    return translator


def get_lang (lang):
    """Return lang if it is supported, or the default language."""
    if lang in supported_languages:
        return lang
    return default_language


def get_headers_lang (headers):
    """Return preferred supported language in given HTTP headers."""
    if 'Accept-Language' not in headers:
        return default_language
    languages = headers['Accept-Language'].split(",")
    # sort with preference values
    pref_languages = []
    for lang in languages:
        pref = 1.0
        if ";" in lang:
            lang, _pref = lang.split(';', 1)
            try:
                pref = float(_pref)
            except ValueError:
                pass
        pref_languages.append((pref, lang))
    pref_languages.sort()
    # search for lang
    for lang in (x[1] for x in pref_languages):
        if lang in supported_languages:
            return lang
    return default_language


def get_locale ():
    """Return current configured locale."""
    loc, encoding = locale.getlocale(category=locale.LC_ALL)
    if loc is None:
        return ('C', 'ascii')
    loc = locale.normalize(loc)
    # split up the locale into its base components
    pos = loc.find('@')
    if pos >= 0:
        loc = loc[:pos]
    pos = loc.find('.')
    if pos >= 0:
        loc = loc[:pos]
    pos = loc.find('_')
    if pos >= 0:
        loc = loc[:pos]
    return (loc, encoding)


lang_names = {
    'en': u'English',
    'de': u'Deutsch',
}
lang_transis = {
    'de': {'en': u'German'},
    'en': {'de': u'Englisch'},
}

def lang_name (lang):
    """Return full name of given language."""
    return lang_names[lang]


def lang_trans (lang, curlang):
    """Return translated full name of given language."""
    return lang_transis[lang][curlang]

## vim:ts=4:et:nowrap
"""i18n (multiple language) support.  Reads .mo files from GNU gettext msgfmt

If you want to prepare your Python programs for i18n you could simply
add the following lines to the top of a BASIC_MAIN module of your py-program:
    try:
        import fintl
        gettext = fintl.gettext
        fintl.bindtextdomain(YOUR_PROGRAM, YOUR_LOCALEDIR)
        fintl.textdomain(YOUR_PROGRAM)
    except ImportError:
        def gettext(msg):
            return msg
    _ = gettext
and/or also add the following to the top of any module containing messages:
    import BASIC_MAIN
    _ = BASIC_MAIN.gettext
            
Now you could use _("....") everywhere instead of "...." for message texts.

Once you have written your internationalized program, you can use
the suite of utility programs contained in the GNU gettext package to aid
the translation into other languages.  

You ARE NOT REQUIRED to release the sourcecode of your program, since 
linking of your program against GPL code is avoided by this module.  
Although it is possible to use the GNU gettext library by using the 
*intl.so* module written by Martin von Löwis if this is available.  But it is
not required to use it in the  first place.
"""
# Copyright 1999 by <mailto: pf@artcom-gmbh.de> (Peter Funk)
#  
#                         All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies.

# ArtCom GmbH AND Peter Funk DISCLAIMS ALL WARRANTIES WITH REGARD TO
# THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS, IN NO EVENT SHALL ArtCom GmBH or Peter Funk BE LIABLE
# FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
# AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING
# OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

_default_localedir = '/usr/share/locale'
_default_domain = 'python'

# check out, if Martin v. Löwis 'intl' module interface to the GNU gettext
# library is available and use it only, if it is available: 
try:
    from intl import *
except ImportError:
    # now do what the gettext library provides in pure Python:
    error = 'fintl.error'
    # some globals preserving state:
    _languages = []
    _default_mo = None # This is default message outfile used by 'gettext'
    _loaded_mos = {}   # This is a dictionary of loaded message output files

    # some small little helper routines:
    def _check_env():
        """examine language enviroment variables and return list of languages"""
        # TODO: This should somehow try to find out locale information on
        #       Non-unix platforms like WinXX and MacOS.  Suggestions welcome!
        languages = []
        import os, string
        for envvar in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
            if os.environ.has_key(envvar):
                languages = string.split(os.environ[envvar], ':')
                break
        # use locale 'C' as default fallback:
        if 'C' not in _languages:
            languages.append('C')
        return languages

    # Utility function used to decode binary .mo file header and seek tables:
    def _decode_Word(bin):
        # This assumes little endian (intel, vax) byte order.
        return  ord(bin[0])        + (ord(bin[1]) <<  8) + \
               (ord(bin[2]) << 16) + (ord(bin[3]) << 24)

    # Now the methods designed to be used from outside:

    def gettext(message):
        """return localized version of a 'message' string"""
        if _default_mo is None: 
            textdomain()
        return _default_mo.gettext(message)

    _ = gettext

    def dgettext(domain, message):
        """like gettext but looks up 'message' in a special 'domain'"""
        # This may useful for larger software systems
        if not _loaded_mos.has_key(domain):
            raise error, "No '" + domain + "' message domain"
        return _loaded_mos[domain].gettext(message)

    class _MoDict:
        """read a .mo file into a python dictionary"""
        __MO_MAGIC = 0x950412de # Magic number of .mo files
        def __init__(self, domain=_default_domain, localedir=_default_localedir):
            global _languages
            self.catalog = {}
            self.domain = domain
            self.localedir = localedir
            # delayed access to environment variables:
            if not _languages:
                _languages = _check_env()
            for self.lang in _languages:
                if self.lang == 'C':
                    return
                mo_filename = "%s//%s/LC_MESSAGES/%s.mo" % (
                                                  localedir, self.lang, domain)
                try:
                     buffer = open(mo_filename, "rb").read()
                     break
                except IOError:
                     pass
            else:
                return # assume C locale
            # Decode the header of the .mo file (5 little endian 32 bit words):
            if _decode_Word(buffer[:4]) != self.__MO_MAGIC :
                raise error, '%s seems not be a valid .mo file' % mo_filename
            self.mo_version = _decode_Word(buffer[4:8])
            num_messages    = _decode_Word(buffer[8:12])
            master_index    = _decode_Word(buffer[12:16])
            transl_index    = _decode_Word(buffer[16:20])
            buf_len = len(buffer)
            # now put all messages from the .mo file buffer in the catalog dict:
            for i in xrange(0, num_messages):
                start_master= _decode_Word(buffer[master_index+4:master_index+8])
                end_master  = start_master + \
                              _decode_Word(buffer[master_index:master_index+4])
                start_transl= _decode_Word(buffer[transl_index+4:transl_index+8])
                end_transl  = start_transl + \
                              _decode_Word(buffer[transl_index:transl_index+4])
                if end_master <= buf_len and end_transl <= buf_len:
                    self.catalog[buffer[start_master:end_master]]=\
                                 buffer[start_transl:end_transl]
                else: 
                    raise error, ".mo file '%s' is corrupt" % mo_filename
                # advance to the next entry in seek tables:
                master_index= master_index + 8
                transl_index= transl_index + 8

        def gettext(self, message):
            """return the translation of a given message"""
            try:
                return self.catalog[message]
            except KeyError:
                return message
        # _MoDict instances may be also accessed using mo[msg] or mo(msg):
        __getitem = gettext
        __call__ = gettext

    def textdomain(domain=_default_domain):
        """Sets the 'domain' to be used by this program. Defaults to 'python'"""
        global _default_mo
        if not _loaded_mos.has_key(domain):
             _loaded_mos[domain] = _MoDict(domain)
        _default_mo = _loaded_mos[domain]

    def bindtextdomain(domain, localedir=_default_localedir):
        global _default_mo
        if not _loaded_mos.has_key(domain):
            _loaded_mos[domain] = _MoDict(domain, localedir)
        if _default_mo is not None: 
            _default_mo = _loaded_mos[domain]

    def translator(domain=_default_domain, localedir=_default_localedir):
        """returns a gettext compatible function object
        
           which is bound to the domain given as parameter"""
        pass  # TODO implement this 

def _testdriver(argv):
    message   = ""
    domain    = _default_domain
    localedir = _default_localedir
    if len(argv) > 1:
        message = argv[1]
        if len(argv) > 2:
            domain = argv[2]
            if len(argv) > 3:
                localedir = argv[3]
    # now perform some testing of this module:
    bindtextdomain(domain, localedir)
    textdomain(domain)
    info = gettext('')  # this is where special info is often stored
    if info:
        print ".mo file for domain %s in %s contains:" % (domain, localedir)
        print info
    else:
        print ".mo file contains no info"
    if message:
        print "Translation of '"+ message+ "' is '"+ _(message)+ "'"
    else:
        for msg in ("Cancel", "No", "OK", "Quit", "Yes"):
            print "Translation of '"+ msg + "' is '"+ _(msg)+ "'"

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and (sys.argv[1] == "-h" or sys.argv[1] == "-?"):
        print "Usage :", sys.argv[0], "[ MESSAGE [ DOMAIN [ LOCALEDIR ]]]"
    _testdriver(sys.argv)

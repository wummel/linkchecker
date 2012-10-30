# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
#   miniboa/telnet.py
#   Copyright 2009 Jim Storch
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain a
#   copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#------------------------------------------------------------------------------

"""
Manage one Telnet client connected via a TCP/IP socket.
"""

import socket
import time

from miniboa.error import BogConnectionLost
from miniboa.xterm import colorize
from miniboa.xterm import word_wrap


#---[ Telnet Notes ]-----------------------------------------------------------
# (See RFC 854 for more information)
#
# Negotiating a Local Option
# --------------------------
#
# Side A begins with:
#
#    "IAC WILL/WONT XX"   Meaning "I would like to [use|not use] option XX."
#
# Side B replies with either:
#
#    "IAC DO XX"     Meaning "OK, you may use option XX."
#    "IAC DONT XX"   Meaning "No, you cannot use option XX."
#
#
# Negotiating a Remote Option
# ----------------------------
#
# Side A begins with:
#
#    "IAC DO/DONT XX"  Meaning "I would like YOU to [use|not use] option XX."
#
# Side B replies with either:
#
#    "IAC WILL XX"   Meaning "I will begin using option XX"
#    "IAC WONT XX"   Meaning "I will not begin using option XX"
#
#
# The syntax is designed so that if both parties receive simultaneous requests
# for the same option, each will see the other's request as a positive
# acknowledgement of it's own.
#
# If a party receives a request to enter a mode that it is already in, the
# request should not be acknowledged.

## Where you see DE in my comments I mean 'Distant End', e.g. the client.

UNKNOWN = -1

#--[ Telnet Commands ]---------------------------------------------------------

SE      = chr(240)      # End of subnegotiation parameters
NOP     = chr(241)      # No operation
DATMK   = chr(242)      # Data stream portion of a sync.
BREAK   = chr(243)      # NVT Character BRK
IP      = chr(244)      # Interrupt Process
AO      = chr(245)      # Abort Output
AYT     = chr(246)      # Are you there
EC      = chr(247)      # Erase Character
EL      = chr(248)      # Erase Line
GA      = chr(249)      # The Go Ahead Signal
SB      = chr(250)      # Sub-option to follow
WILL    = chr(251)      # Will; request or confirm option begin
WONT    = chr(252)      # Wont; deny option request
DO      = chr(253)      # Do = Request or confirm remote option
DONT    = chr(254)      # Don't = Demand or confirm option halt
IAC     = chr(255)      # Interpret as Command
SEND    = chr(001)      # Sub-process negotiation SEND command
IS      = chr(000)      # Sub-process negotiation IS command

#--[ Telnet Options ]----------------------------------------------------------

BINARY  = chr(  0)      # Transmit Binary
ECHO    = chr(  1)      # Echo characters back to sender
RECON   = chr(  2)      # Reconnection
SGA     = chr(  3)      # Suppress Go-Ahead
TTYPE   = chr( 24)      # Terminal Type
NAWS    = chr( 31)      # Negotiate About Window Size
LINEMO  = chr( 34)      # Line Mode


#-----------------------------------------------------------------Telnet Option

class TelnetOption(object):
    """
    Simple class used to track the status of an extended Telnet option.
    """
    def __init__(self):
        self.local_option = UNKNOWN     # Local state of an option
        self.remote_option = UNKNOWN    # Remote state of an option
        self.reply_pending = False      # Are we expecting a reply?


#------------------------------------------------------------------------Telnet

class TelnetClient(object):

    """
    Represents a client connection via Telnet.

    First argument is the socket discovered by the Telnet Server.
    Second argument is the tuple (ip address, port number).
    """

    def __init__(self, sock, addr_tup):
        self.protocol = 'telnet'
        self.active = True          # Turns False when the connection is lost
        self.sock = sock            # The connection's socket
        self.fileno = sock.fileno() # The socket's file descriptor
        self.address = addr_tup[0]  # The client's remote TCP/IP address
        self.port = addr_tup[1]     # The client's remote port
        self.terminal_type = 'unknown client' # set via request_terminal_type()
        self.use_ansi = True
        self.columns = 80
        self.rows = 24
        self.send_pending = False
        self.send_buffer = ''
        self.recv_buffer = ''
        self.bytes_sent = 0
        self.bytes_received = 0
        self.cmd_ready = False
        self.command_list = []
        self.connect_time = time.time()
        self.last_input_time = time.time()

        ## State variables for interpreting incoming telnet commands
        self.telnet_got_iac = False # Are we inside an IAC sequence?
        self.telnet_got_cmd = None  # Did we get a telnet command?
        self.telnet_got_sb = False  # Are we inside a subnegotiation?
        self.telnet_opt_dict = {}   # Mapping for up to 256 TelnetOptions
        self.telnet_echo = False    # Echo input back to the client?
        self.telnet_echo_password = False  # Echo back '*' for passwords?
        self.telnet_sb_buffer = ''  # Buffer for sub-negotiations

#    def __del__(self):

#        print "Telnet destructor called"
#        pass

    def get_command(self):
        """
        Get a line of text that was received from the DE. The class's
        cmd_ready attribute will be true if lines are available.
        """
        cmd = None
        count = len(self.command_list)
        if count > 0:
            cmd = self.command_list.pop(0)
        ## If that was the last line, turn off lines_pending
        if count == 1:
            self.cmd_ready = False
        return cmd

    def send(self, text):
        """
        Send raw text to the distant end.
        """
        if text:
            self.send_buffer += text.replace('\n', '\r\n')
            self.send_pending = True

    def send_cc(self, text):
        """
        Send text with caret codes converted to ansi.
        """
        self.send(colorize(text, self.use_ansi))

    def send_wrapped(self, text):
        """
        Send text padded and wrapped to the user's screen width.
        """
        lines = word_wrap(text, self.columns)
        for line in lines:
            self.send_cc(line + '\n')

    def deactivate(self):
        """
        Set the client to disconnect on the next server poll.
        """
        self.active = False

    def addrport(self):
        """
        Return the DE's IP address and port number as a string.
        """
        return "%s:%s" % (self.address, self.port)

    def idle(self):
        """
        Returns the number of seconds that have elasped since the DE
        last sent us some input.
        """
        return time.time() - self.last_input_time

    def duration(self):
        """
        Returns the number of seconds the DE has been connected.
        """
        return time.time() - self.connect_time

    def request_do_sga(self):
        """
        Request DE to Suppress Go-Ahead.  See RFC 858.
        """
        self._iac_do(SGA)
        self._note_reply_pending(SGA, True)

    def request_will_echo(self):
        """
        Tell the DE that we would like to echo their text.  See RFC 857.
        """
        self._iac_will(ECHO)
        self._note_reply_pending(ECHO, True)
        self.telnet_echo = True

    def request_wont_echo(self):
        """
        Tell the DE that we would like to stop echoing their text.
        See RFC 857.
        """
        self._iac_wont(ECHO)
        self._note_reply_pending(ECHO, True)
        self.telnet_echo = False

    def password_mode_on(self):
        """
        Tell DE we will echo (but don't) so typed passwords don't show.
        """
        self._iac_will(ECHO)
        self._note_reply_pending(ECHO, True)

    def password_mode_off(self):
        """
        Tell DE we are done echoing (we lied) and show typing again.
        """
        self._iac_wont(ECHO)
        self._note_reply_pending(ECHO, True)

    def request_naws(self):
        """
        Request to Negotiate About Window Size.  See RFC 1073.
        """
        self._iac_do(NAWS)
        self._note_reply_pending(NAWS, True)

    def request_terminal_type(self):
        """
        Begins the Telnet negotiations to request the terminal type from
        the client.  See RFC 779.
        """
        self._iac_do(TTYPE)
        self._note_reply_pending(TTYPE, True)

    def socket_send(self):
        """
        Called by TelnetServer when send data is ready.
        """
        if len(self.send_buffer):
            try:
                sent = self.sock.send(self.send_buffer)
            except socket.error, err:
                print("!! SEND error '%d:%s' from %s" % (err[0], err[1],
                    self.addrport()))
                self.active = False
                return
            self.bytes_sent += sent
            self.send_buffer = self.send_buffer[sent:]
        else:
            self.send_pending = False

    def socket_recv(self):
        """
        Called by TelnetServer when recv data is ready.
        """
        try:
            data = self.sock.recv(2048)
        except socket.error, ex:
            print ("?? socket.recv() error '%d:%s' from %s" %
                (ex[0], ex[1], self.addrport()))
            raise BogConnectionLost()

        ## Did they close the connection?
        size = len(data)
        if size == 0:
            raise BogConnectionLost()

        ## Update some trackers
        self.last_input_time = time.time()
        self.bytes_received += size

        ## Test for telnet commands
        for byte in data:
            self._iac_sniffer(byte)

        ## Look for newline characters to get whole lines from the buffer
        while True:
            mark = self.recv_buffer.find('\n')
            if mark == -1:
                break
            cmd = self.recv_buffer[:mark].strip()
            self.command_list.append(cmd)
            self.cmd_ready = True
            self.recv_buffer = self.recv_buffer[mark+1:]

    def _recv_byte(self, byte):
        """
        Non-printable filtering currently disabled because it did not play
        well with extended character sets.
        """
        ## Filter out non-printing characters
        #if (byte >= ' ' and byte <= '~') or byte == '\n':
        if self.telnet_echo:
            self._echo_byte(byte)
        self.recv_buffer += byte

    def _echo_byte(self, byte):
        """
        Echo a character back to the client and convert LF into CR\LF.
        """
        if byte == '\n':
            self.send_buffer += '\r'
        if self.telnet_echo_password:
            self.send_buffer += '*'
        else:
            self.send_buffer += byte

    def _iac_sniffer(self, byte):
        """
        Watches incomming data for Telnet IAC sequences.
        Passes the data, if any, with the IAC commands stripped to
        _recv_byte().
        """
        ## Are we not currently in an IAC sequence coming from the DE?
        if self.telnet_got_iac is False:

            if byte == IAC:
                ## Well, we are now
                self.telnet_got_iac = True
                return

            ## Are we currenty in a sub-negotion?
            elif self.telnet_got_sb is True:
                ## Sanity check on length
                if len(self.telnet_sb_buffer) < 64:
                    self.telnet_sb_buffer += byte
                else:
                    self.telnet_got_sb = False
                    self.telnet_sb_buffer = ""
                return

            else:
                ## Just a normal NVT character
                self._recv_byte(byte)
                return

        ## Byte handling when already in an IAC sequence sent from the DE

        else:

            ## Did we get sent a second IAC?
            if byte == IAC and self.telnet_got_sb is True:
                ## Must be an escaped 255 (IAC + IAC)
                self.telnet_sb_buffer += byte
                self.telnet_got_iac = False
                return

            ## Do we already have an IAC + CMD?
            elif self.telnet_got_cmd:
                ## Yes, so handle the option
                self._three_byte_cmd(byte)
                return

            ## We have IAC but no CMD
            else:

                ## Is this the middle byte of a three-byte command?
                if byte == DO:
                    self.telnet_got_cmd = DO
                    return

                elif byte == DONT:
                    self.telnet_got_cmd = DONT
                    return

                elif byte == WILL:
                    self.telnet_got_cmd = WILL
                    return

                elif byte == WONT:
                    self.telnet_got_cmd = WONT
                    return

                else:
                    ## Nope, must be a two-byte command
                    self._two_byte_cmd(byte)


    def _two_byte_cmd(self, cmd):
        """
        Handle incoming Telnet commands that are two bytes long.
        """
        #print "got two byte cmd %d" % ord(cmd)

        if cmd == SB:
            ## Begin capturing a sub-negotiation string
            self.telnet_got_sb = True
            self.telnet_sb_buffer = ''

        elif cmd == SE:
            ## Stop capturing a sub-negotiation string
            self.telnet_got_sb = False
            self._sb_decoder()

        elif cmd == NOP:
            pass

        elif cmd == DATMK:
            pass

        elif cmd == IP:
            pass

        elif cmd == AO:
            pass

        elif cmd == AYT:
            pass

        elif cmd == EC:
            pass

        elif cmd == EL:
            pass

        elif cmd == GA:
            pass

        else:
            print "2BC: Should not be here."

        self.telnet_got_iac = False
        self.telnet_got_cmd = None

    def _three_byte_cmd(self, option):
        """
        Handle incoming Telnet commmands that are three bytes long.
        """
        cmd = self.telnet_got_cmd
        #print "got three byte cmd %d:%d" % (ord(cmd), ord(option))

        ## Incoming DO's and DONT's refer to the status of this end

        #---[ DO ]-------------------------------------------------------------

        if cmd == DO:

            if option == BINARY:

                if self._check_reply_pending(BINARY):
                    self._note_reply_pending(BINARY, False)
                    self._note_local_option(BINARY, True)

                elif (self._check_local_option(BINARY) is False or
                        self._check_local_option(BINARY) is UNKNOWN):
                    self._note_local_option(BINARY, True)
                    self._iac_will(BINARY)
                    ## Just nod

            elif option == ECHO:

                if self._check_reply_pending(ECHO):
                    self._note_reply_pending(ECHO, False)
                    self._note_local_option(ECHO, True)

                elif (self._check_local_option(ECHO) is False or
                        self._check_local_option(ECHO) is UNKNOWN):
                    self._note_local_option(ECHO, True)
                    self._iac_will(ECHO)
                    self.telnet_echo = True

            elif option == SGA:

                if self._check_reply_pending(SGA):
                    self._note_reply_pending(SGA, False)
                    self._note_local_option(SGA, True)

                elif (self._check_local_option(SGA) is False or
                        self._check_local_option(SGA) is UNKNOWN):
                    self._note_local_option(SGA, True)
                    self._iac_will(SGA)
                    ## Just nod

            else:

                ## ALL OTHER OTHERS = Default to refusing once
                if self._check_local_option(option) is UNKNOWN:
                    self._note_local_option(option, False)
                    self._iac_wont(option)


        #---[ DONT ]-----------------------------------------------------------

        elif cmd == DONT:

            if option == BINARY:

                if self._check_reply_pending(BINARY):
                    self._note_reply_pending(BINARY, False)
                    self._note_local_option(BINARY, False)

                elif (self._check_local_option(BINARY) is True or
                        self._check_local_option(BINARY) is UNKNOWN):
                    self._note_local_option(BINARY, False)
                    self._iac_wont(BINARY)
                    ## Just nod

            elif option == ECHO:

                if self._check_reply_pending(ECHO):
                    self._note_reply_pending(ECHO, False)
                    self._note_local_option(ECHO, True)
                    self.telnet_echo = False

                elif (self._check_local_option(BINARY) is True or
                        self._check_local_option(BINARY) is UNKNOWN):
                    self._note_local_option(ECHO, False)
                    self._iac_wont(ECHO)
                    self.telnet_echo = False

            elif option == SGA:

                if self._check_reply_pending(SGA):
                    self._note_reply_pending(SGA, False)
                    self._note_local_option(SGA, False)

                elif (self._check_remote_option(SGA) is True or
                        self._check_remote_option(SGA) is UNKNOWN):
                    self._note_local_option(SGA, False)
                    self._iac_will(SGA)
                    ## Just nod

            else:

                ## ALL OTHER OPTIONS = Default to ignoring
                pass


        ## Incoming WILL's and WONT's refer to the status of the DE

        #---[ WILL ]-----------------------------------------------------------

        elif cmd == WILL:

            if option == ECHO:

                ## Nutjob DE offering to echo the server...
                if self._check_remote_option(ECHO) is UNKNOWN:
                    self._note_remote_option(ECHO, False)
                    # No no, bad DE!
                    self._iac_dont(ECHO)

            elif option == NAWS:

                if self._check_reply_pending(NAWS):
                    self._note_reply_pending(NAWS, False)
                    self._note_remote_option(NAWS, True)
                    ## Nothing else to do, client follow with SB

                elif (self._check_remote_option(NAWS) is False or
                        self._check_remote_option(NAWS) is UNKNOWN):
                    self._note_remote_option(NAWS, True)
                    self._iac_do(NAWS)
                    ## Client should respond with SB

            elif option == SGA:

                if self._check_reply_pending(SGA):
                    self._note_reply_pending(SGA, False)
                    self._note_remote_option(SGA, True)

                elif (self._check_remote_option(SGA) is False or
                        self._check_remote_option(SGA) is UNKNOWN):
                    self._note_remote_option(SGA, True)
                    self._iac_do(SGA)
                    ## Just nod

            elif option == TTYPE:

                if self._check_reply_pending(TTYPE):
                    self._note_reply_pending(TTYPE, False)
                    self._note_remote_option(TTYPE, True)
                    ## Tell them to send their terminal type
                    self.send('%c%c%c%c%c%c' % (IAC, SB, TTYPE, SEND, IAC, SE))

                elif (self._check_remote_option(TTYPE) is False or
                        self._check_remote_option(TTYPE) is UNKNOWN):
                    self._note_remote_option(TTYPE, True)
                    self._iac_do(TTYPE)


        #---[ WONT ]-----------------------------------------------------------

        elif cmd == WONT:

            if option == ECHO:

                ## DE states it wont echo us -- good, they're not suppose to.
                if self._check_remote_option(ECHO) is UNKNOWN:
                    self._note_remote_option(ECHO, False)
                    self._iac_dont(ECHO)

            elif option == SGA:

                if self._check_reply_pending(SGA):
                    self._note_reply_pending(SGA, False)
                    self._note_remote_option(SGA, False)

                elif (self._check_remote_option(SGA) is True or
                        self._check_remote_option(SGA) is UNKNOWN):
                    self._note_remote_option(SGA, False)
                    self._iac_dont(SGA)

                if self._check_reply_pending(TTYPE):
                    self._note_reply_pending(TTYPE, False)
                    self._note_remote_option(TTYPE, False)

                elif (self._check_remote_option(TTYPE) is True or
                        self._check_remote_option(TTYPE) is UNKNOWN):
                    self._note_remote_option(TTYPE, False)
                    self._iac_dont(TTYPE)

        else:
            print "3BC: Should not be here."

        self.telnet_got_iac = False
        self.telnet_got_cmd = None

    def _sb_decoder(self):
        """
        Figures out what to do with a received sub-negotiation block.
        """
        #print "at decoder"
        bloc = self.telnet_sb_buffer
        if len(bloc) > 2:

            if bloc[0] == TTYPE and bloc[1] == IS:
                self.terminal_type = bloc[2:]
                #print "Terminal type = '%s'" % self.terminal_type

            if bloc[0] == NAWS:
                if len(bloc) != 5:
                    print "Bad length on NAWS SB:", len(bloc)
                else:
                    self.columns = (256 * ord(bloc[1])) + ord(bloc[2])
                    self.rows = (256 * ord(bloc[3])) + ord(bloc[4])

                #print "Screen is %d x %d" % (self.columns, self.rows)

        self.telnet_sb_buffer = ''


    #---[ State Juggling for Telnet Options ]----------------------------------

    ## Sometimes verbiage is tricky.  I use 'note' rather than 'set' here
    ## because (to me) set infers something happened.

    def _check_local_option(self, option):
        """Test the status of local negotiated Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        return self.telnet_opt_dict[option].local_option

    def _note_local_option(self, option, state):
        """Record the status of local negotiated Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        self.telnet_opt_dict[option].local_option = state

    def _check_remote_option(self, option):
        """Test the status of remote negotiated Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        return self.telnet_opt_dict[option].remote_option

    def _note_remote_option(self, option, state):
        """Record the status of local negotiated Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        self.telnet_opt_dict[option].remote_option = state

    def _check_reply_pending(self, option):
        """Test the status of requested Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        return self.telnet_opt_dict[option].reply_pending

    def _note_reply_pending(self, option, state):
        """Record the status of requested Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        self.telnet_opt_dict[option].reply_pending = state


    #---[ Telnet Command Shortcuts ]-------------------------------------------

    def _iac_do(self, option):
        """Send a Telnet IAC "DO" sequence."""
        self.send('%c%c%c' % (IAC, DO, option))

    def _iac_dont(self, option):
        """Send a Telnet IAC "DONT" sequence."""
        self.send('%c%c%c' % (IAC, DONT, option))

    def _iac_will(self, option):
        """Send a Telnet IAC "WILL" sequence."""
        self.send('%c%c%c' % (IAC, WILL, option))

    def _iac_wont(self, option):
        """Send a Telnet IAC "WONT" sequence."""
        self.send('%c%c%c' % (IAC, WONT, option))

#!/usr/bin/env python
#     DStat Interface - An interface for the open hardware DStat potentiostat
#     Copyright (C) 2014  Michael D. M. Dryden - 
#     Wheeler Microfluidics Laboratory <http://microfluidics.utoronto.ca>
#         
#     
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#     
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#     
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

import zmq

#signals
CONREQ = "0"
CONREP = "1"
STARTEXP = "start"
START_REP = "started"
EXP_FINISH_REQ = "notify_completion"
EXPFINISHED = "completed"
INVAL_CMD = "99"

#States
RECV = 0
SEND = 1

class microdropConnection(object):
    """Manages microdrop connection over TCP with zmq"""
    def __init__(self, port=6789):
        """Create zmq context and bind to port. Should be called manually
        to reinitialize if reset is called.
        
        Keyword arguments:
        port -- the TCP to bind to on localhost
        """
        self.port = port
        self.connected = False
        self.state = RECV
    
        self.ctx = zmq.Context()
        self.soc = zmq.Socket(self.ctx, zmq.REP)
        self.soc.bind("".join(['tcp://*:', str(self.port)]))
    
    def listen(self):
        """Perform non-blocking recv on zmq port. self.state must be RECV.
        Returns a tuple:
        [0] -- True if a message was received, False otherwise.
        [1] -- The recieved message or "" if no message received.
        """
        if self.state == SEND:
            print "WAR: [uDrop-listen] Connection state invalid, resetting..."
            # self.reset()
            # self.__init__(self.port)
            return (False, "")
			
        try:
            message = self.soc.recv(flags=zmq.NOBLOCK, copy=True)
            self.state = SEND
            return (True, message)
        except zmq.Again:
            return (False, "")

    def reply(self, data):
        """Sends a reply on zmq port. self.state must be SEND.
        
        Arguments:
        data -- a str to be sent
        """
        if self.state == RECV:
            print "WAR: [uDrop-reply] Connection state invalid, resetting..."
            self.reset()
            self.__init__(self.port)
            return False
        self.state = RECV
        self.soc.send(data)
        return True
        
    def reset(self):
        """Reset zmq interface. Must call __init__ again to reinitialize."""
        self.soc.unbind("".join(['tcp://*:', str(self.port)]))
        del self.soc
        del self.ctx

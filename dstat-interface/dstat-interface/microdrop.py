import zmq
import zmq.error

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
            print "WAR: Microdrop Connection state invalid, resetting..."
            self.reset()
            self.__init__(self.port)
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
            print "WAR: Microdrop Connection state invalid, resetting..."
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
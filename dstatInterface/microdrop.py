import zmq
import zmq.error

#signals
CONREQ = "0"
CONREP = "1"
STARTEXP = "10"
EXPFINISHED = "11"
INVAL_CMD = "99"

#States
RECV = 0
SEND = 1

class microdropConnection:

    def __init__(self, port=6789):
        self.port = port
        self.connected = False
        self.state = RECV
    
        self.ctx = zmq.Context()
        self.soc = zmq.Socket(self.ctx, zmq.REP)
        self.soc.bind("".join(['tcp://*:',str(self.port)]))
    
    def listen(self):
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
        if self.state == RECV:
            print "WAR: Microdrop Connection state invalid, resetting..."
            self.reset()
            self.__init__(self.port)
            return False
        self.state = RECV
        self.soc.send(data)
        return True
        
    def reset(self):
        self.soc.unbind("".join(['tcp://*:',str(self.port)]))
        del self.soc
        del self.ctx

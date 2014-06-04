import socket

class Irc:

    def __init__(self, host, port, name, channel):
        self.host = host
        self.port = port
        self.name = name
        self.channel = channel
        self.buf = ''
        self.client = socket.socket()

    def connect(self):
        self.client.connect((self.host, self.port))
        self.send('NICK', self.name)
        self.send('USER', self.name, '8', '*', self.name)
        self.send('JOIN', self.channel)

    def send(self, *data):
        line = ' '.join(data) + '\r\n'
        self.client.send(line.encode())

    def receive(self):
        self.buf += self.client.recv(4096).decode()
        if '\r\n' in self.buf:
            line = self.buf.split('\r\n')
            self.buf = line[-1]
            line = line[:-1]
            return line
import re, irc, db, threading, config

class Pymarket:

    def __init__(self, serverName, connection):
        self.server = serverName
        self.irc = connection
        self.users = set()
        self.handlers = {
            'PRIVMSG': self.message,
            'NOTICE': self.notice,
            'JOIN': self.join,
            'QUIT': self.leave,
            'PART': self.leave,
            'KICK': self.kick,
            'KILL': self.kick,
            'NICK': self.nick,
            '353': self.names
        }

    def parseMessage(self, line):
        values = {}
        if line[0] == ':':
            values['prefix'], line = line[1:].split(' ', 1)
        line = line.split(' ', 1)
        if len(line) > 1:
            values['command'] = line[0]
            values['params'] = line[1]
        elif len(line) == 1:
            values['command'] = line[0]

        if 'prefix' in values and '!' in values['prefix']:
            values['nick'] = values['prefix'].split('!', 1)[0]
        if 'params' in values and ' :' in values['params']:
            values['params'], values['text'] = values['params'].split(' :', 1)
            values['params'] = values['params'].split()
            values['target'] = values['params'].pop(0)
            if len(values['params']) > 0:
                values['extra'] = values['params'].pop(0)
        choice = self.handlers.get(values['command'])
        if choice:
            choice(values)

    def message(self, values):
        if values['target'] == self.irc.name:
            self.notice(values)
            return
        try:
            command = values['text'].split()[0]
        except:
            return
        if '+=' in command:
            rcv, credits = command.split('+=', 1)
            try:
                credits = int(credits)
                if rcv in self.users and credits > 0 and values['nick'] != rcv:
                    if db.transfer(self.server, values['nick'], rcv, credits):
                        self.irc.send(
                            'PRIVMSG', values['target'], 
                            ':Credits transferred from', values['nick'], 
                            'to', rcv + ':', str(credits))
                    else:
                        self.irc.send(
                            'PRIVMSG', values['target'], 
                            ':' + values['nick'] + ': Not enough credits.')
            except ValueError:
                pass
        test = re.match('(\\w+)[:,]?', command)
        if test:
            if self.irc.name == test.group(1) and 'help' in values['text']:
                self.irc.send(
                    'PRIVMSG', values['target'], 
                    ':' + '\"<nick>+=X\" will transfer X credits to <nick>.')
                self.irc.send(
                    'PRIVMSG', values['target'], 
                    ':' + 'PM or NOTICE PyMarket with '
                    '<nick> to see <nick>\'s credits.')

    def notice(self, values):
        numCredits = None
        if db.checkBal(self.server, values['text']):
            numCredits = db.checkBal(self.server, values['text'])
        elif values['text'] in self.users:
            numCredits = 15
        if numCredits != None:
            self.irc.send(
                'NOTICE', values['nick'], ':' + values['text'], 
                'has', str(numCredits), 'credits.')

    def join(self, values):
        self.users.add(values['nick'])

    def leave(self, values):
        if values['nick'] in self.users:
            self.users.remove(values['nick'])

    def kick(self, values):
        if values['extra'] in self.users:
            self.users.remove(values['extra'])

    def nick(self, values):
        self.users.add(values['text'])
        if values['nick'] in self.users:
            self.users.remove(values['nick'])
        
    def names(self, values):
        for nick in values['text'].split():
            self.users.add(re.match('^[~&@%+]?(.+)$', nick).group(1))

def main():

    def startBot(bot):
        bot.irc.connect()
        while True:
            lines = bot.irc.receive()
            for text in lines:
                text = text.decode('utf-8', 'replace')
                print(text)
                bot.parseMessage(text)

    for server in config.servers:
        connection = irc.Irc(
            server['url'], server['port'],
            server['nick'], server['channels'])
        bot = Pymarket(server['name'], connection)
        threading.Thread(target=startBot, args=(bot,)).start()
        
if __name__ == '__main__':
    main()

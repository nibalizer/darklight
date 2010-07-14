#!/usr/bin/env python

import base64
import os.path

import twisted.protocols.basic

from darklight.core import DarkCache, DarkConf, DarkTimer

class DarkServerProtocol(twisted.protocols.basic.LineReceiver):

    def __init__(self):
        print "Protocol created..."
        self.authorized = False

    def checkapi(self, tokens):
        self.sendLine("API 1")

    def bai(self, tokens):
        self.transport.loseConnection()

    def fail(self, tokens):
        self.transport.loseConnection()

    def hai(self, tokens):
        self.authorized = True
        self.sendLine("OHAI")

    def kthnxbai(self, tokens):
        self.sendLine("BAI")
        self.bai(tokens)

    def sendpeze(self, tokens):
        """
        SENDPEZE <hash> <size> <piece>

        The hash is some form of TTH hash. The size and piece are ASCII
        decimal.
        """

        try:
            h, size, piece = tokens
            size = int(size)
            piece = int(piece)
        except ValueError:
            self.error()
            return

        l = self.factory.cache.search((h, size))
        if len(l) == 1:
            buf = self.factory.cache.getdata(l[0], piece)
            if not buf:
                print "File buffer was bad..."
                self.error()
                return
            i, sent = 0, 0
            tth = base64.b32encode(self.factory.cache.getpiece(l[0], piece))
            self.sendLine("K %s %s" % (tth, str(len(buf))))
            self.sendLine(buf)
        else:
            self.error()

    def version(self, tokens):
        self.sendLine("Darklight pre-alpha")

    helpers = {"BAI": bai, "CHECKAPI": checkapi, "FAIL": fail, "HAI": hai,
        "KTHNXBAI": kthnxbai, "SENDPEZE": sendpeze, "VERSION": version}

    def error(self):
        self.sendLine("FAIL")
        self.transport.loseConnection()

    def unknown(self):
        self.sendLine("LOLWUT")
        self.transport.loseConnection()

    def authorize(self, challenge):
        if challenge.strip() == "HAI":
            self.authorized = True
        return self.authorized

    def dispatch(self, line):
        if not self.authorized:
            if not self.authorize(line):
                return

        tokens = [i.strip() for i in line.split(' ')]

        try:
            print "Dispatching '%s'" % line
            self.helpers[tokens[0]](self, tokens[1:])
        except KeyError:
            print "Unknown command '%s'" % tokens[0]
            self.unknown()
        #except:
            #print "Error dispatching '%s'" % line
            #self.error()

    def lineReceived(self, line):
        print "Received line: %s" % line
        self.dispatch(line)

    def sendLine(self, line):
        print "Sending '%s'" % line
        twisted.protocols.basic.LineReceiver.sendLine(self, line)

#!/usr/bin/env python

import os

from cache import DarkCache
from db import DarkDB

import logging
logging.basicConfig(level=logging.DEBUG)

class DarkConf(object):
    """An object that parses configuration."""

    immhash = False
    cache_size = 10 * 1024 * 1024

    def __init__(self):
        self.folders = list()
        self.remotes = list()

    def parse(self, path):
        f = open(os.path.normpath(path))
        for line in f.readlines():
            try:
                if line.startswith("#"):
                    continue
                tokens = [i.strip() for i in line.split(' ')]
                if tokens[0] == "FOLDER":
                    path = os.path.normpath(tokens[1])
                    if os.path.exists(path):
                        self.folders.append(path)
                    else:
                        logging.warning("Path %s does not exist!" % path)
                elif tokens[0] == "CACHE":
                    self.cache_size = int(tokens[1])
                elif tokens[0] == "DB":
                    DarkDB().path = tokens[1]
                elif tokens[0] == "REMOTE":
                    try:
                        self.remotes.append((tokens[1], int(tokens[2])))
                    except IndexError:
                        self.remotes.append((tokens[1], 56789))
                elif tokens[0] == "HASHSTYLE":
                    # "immediate"
                    if tokens[1].startswith("imm"):
                        self.immhash = True
                else:
                    logging.warning("Unknown config line, skipping:")
                    logging.warning("\t%s" % line)
            except IndexError:
                logging.warning("Bad config line:")
                logging.warning("\t%s" % line)

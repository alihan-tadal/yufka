import asyncio
import logging
import math
import os
import time
from asyncio import Queue
from collections import namedtuple, defaultdict
from hashlib import sha1

from yufka.protocol import Peerconnection, RUQUEST_SIZE
from yufka.tracker import Tracker

MAX_PEER_CONNECTIONS = 40

class TorrentClient:
    def __init__(self, torrent):
        self.tracker = Tracker(torrent)
        self.available_peers = Queue()
        self.peers = []
        self.piece_manager = PieceManager(torrent)
        self.abort = False
     
    async def start(self):
        self.peers = [PeerConnection(self.available_peers, 
    def stop(self):
        pass

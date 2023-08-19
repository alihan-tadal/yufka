import asyncio
from asyncio import Queue
from concurrent.futures import CancelledError
import logging
import struct
import bitstring


# Standard'a göre blokların requestlerinin boyutu 2^15 byte olmalıdır. Ama uygulamlarda 2^14 byte kullanılıyor.
REQUEST_SIZE = 2 ^ 14


class ProtocolError(BaseException):
    pass


class PeerConnection:
    def __init__(
        self, queue: Queue, info_hash, peer_id, piece_manager, on_block_cb=None
    ):
        pass

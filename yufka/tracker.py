import random
from struct import unpack
import aiohttp
import logging
import socket
from urllib.parse import urlencode

from . import bencoding


class TrackerResponse:
    def __init__(self, response: dict):
        self.response = response

    @property
    def failure(self):
        if b"failure reason" in self.response:
            return self.response[b"failure reason"].decode("utf-8")
        return None

    @property
    def complete(self) -> int:
        return self.response.get(b"complete", 0)

    @property
    def interval(self):
        return self.response.get(b"interval", 0)

    @property
    def incomplete(self) -> int:
        return self.response.get(b"incomplete", 0)

    @property
    def peers(self):
        peers = self.response[b"peers"]
        if type(peers) == list:
            logging.debug("Peers are in list format")
            peers = [peers[i : i + 6] for i in range(0, len(peers), 6)]
            return [
                (socket.inet_ntoa(peer[:4]), int.from_bytes(peer[4:], "big"))
                for peer in peers
            ]

    def __str__(self):
        return (
            "incomplete: {incomplete}\n"
            "complete: {complete}\n"
            "interval: {interval}\n"
            "peers: {peers}\n".format(
                incomplete=self.incomplete,
                complete=self.complete,
                interval=self.interval,
                peers=", ".join([x for (x, _) in self.peers]),
            )
        )


class Tracker:
    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = _calculate_per_id()
        self.http_client = aiohttp.ClientSession()

    async def connect(self, first: bool = None, uploaded: int = 0, downloaded: int = 0):
        params = {
            "info_hash": self.torrent.info_hash,
            "peer_id": self.peer_id,
            "port": 6889,
            "uploaded": uploaded,
            "downloaded": downloaded,
            "left": self.torrent.length - downloaded,
            "compact": 1,
        }
        if first:
            params["event"] = "started"
        url = self.torrent.announce + "?" + urlencode(params)
        logging.info("Connecting to tracker: %s", url)
        async with self.http_client.get(url) as response:
            if not response.status == 200:
                raise ConnectionError("Tracker response status is not 200")
            data = await response.read()
            self.raise_for_error(data)
            return TrackerResponse(bencoding.Decoder(data).decode())

    def close(self):
        self.http_client.close()

    def raise_for_error(self, tracker_response: bytes):
        try:
            message = tracker_response[b"failure reason"].decode("utf-8")
            if "failure" in message:
                raise ConnectionError(
                    "Unable to connect to tracker: {}".format(message)
                )
        except UnicodeDecodeError:
            return

    def _construct_tracker_parameters(self):
        return {
            "info_hash": self.torrent.info_hash,
            "peer_id": self.peer_id,
            "port": 6889,
            "uploaded": 0,
            "downloaded": 0,
            "left": self.torrent.length,
            "compact": 1,
        }


def _calculate_per_id():
    """
    Read more:
        https://wiki.theory.org/BitTorrentSpecification#peer_id
    """
    return "-PC0001-" + "".join([str(random.randint(0, 9)) for _ in range(12)])


def _decode_port(port):
    """
    Converts a 32-bit packed binary port number to int
    """
    # Convert from C style big-endian encoded as unsigned short
    return unpack(">H", port)[0]

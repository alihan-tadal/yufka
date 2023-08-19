from hashlib import sha1
from collections import namedtuple
from yufka import bencoding


TorrentFile = namedtuple("TorrentFile", ["name", "length"])


class Torrent:
    def __init__(self, filename):
        self.filename = filename
        self.files = []

        with open(self.filename, "rb") as f:
            meta_info = f.read()
            self.meta_info = bencoding.Decoder(meta_info).decode()
            info = bencoding.Encoder(self.meta_info[b"info"]).encode()
            self.info_hash = sha1(info).digest()
            self._identify_files()

    def _identify_files(self):
        if self.multi_file:
            raise RuntimeError("Multi-file torrents are not supported yet.")
        self.files.append(
            TorrentFile(
                self.meta_info[b"info"][b"name"].decode(),
                self.meta_info[b"info"][b"length"],
            )
        )

    @property
    def announce(self) -> str:
        return self.meta_info[b"announce"].decode("utf-8")

    @property
    def multi_file(self) -> bool:
        return b"files" in self.meta_info[b"info"]

    @property
    def piece_length(self):
        return self.meta_info[b"info"][b"piece length"]

    @property
    def total_size(self) -> int:
        if self.multi_file:
            raise RuntimeError("Multi-file torrents are not supported yet.")
        return self.files[0].length

    @property
    def pieces(self):
        data = self.meta_info[b"info"][b"pieces"]
        pieces = []
        offset = 0
        length = len(data)

        while offset < length:
            pieces.append(data[offset : offset + 20])
            offset += 20

        return pieces

    @property
    def output_file(self):
        pass

    @property
    def __str__(self):
        pass

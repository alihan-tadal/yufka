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
        self.my_state = []
        self.peer_state = []
        self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.remote_id = None
        self.writer = None
        self.reader = None
        self.piece_manager = piece_manager
        self.on_block_cb = on_block_cb
        self.future = asyncio.ensure_future(self.run())

    async def _start(self):
        while "stopped" not in self.my_state:
            ip, port = await self.queue.get()
            logging.info(f"Assigned to {ip}:{port}")

            try:
                self.reader, self.writer = await asyncio.open_connection(ip, port)
                logging.info(f"Connection open to {ip}:{port}")
                buffer = await self._handsake()
                self.my_state.append("chocked")
                await self._send_interested()
                self.my_state.append("interested")

                async for message in PeerStreamIterator(self.reader, buffer):
                    if "stopped" in self.my_state:
                        break
                    if type(message) is BitField:
                        self.piece_manager.add_peer(self.remote_id, message.bitfield)
                    elif type(message) is Interested:
                        self.peer_state.append("interested")
                    elif type(message) is NotInterested:
                        if "interested" in self.peer_state:
                            self.peer_state.remove("interested")
                    elif type(message) is Choke:
                        self.my_state.append("choked")
                    elif type(message) is Unchoke:
                        if "choked" in self.my_state:
                            self.my_state.remove("choked")
                    elif type(message) is Have:
                        self.piece_manager.update_peer(self.remote_id, message.index)
                    elif type(message) is KeepAlive:
                        pass
                    elif type(message) is Piece:
                        self.my_state.remove("pending_request")
                        self.on_block_cb(
                            peer_id=self.remote_id,
                            piece_index=message.index,
                            block_offset=message.begin,
                            data=message.block,
                        )
                    elif type(message) is Request:
                        logging.info("Ignoring the received Request message.")
                    elif type(message) is Cancel:
                        logging.info("Ignoring the received Cancel message.")
                    if "choked" not in self.my_state:
                        if "interested" not in self.my_state:
                            if "pending_request" not in self.my_state:
                                self.my_state.append("pending_request")
                                await self._request_piece()
            except ProtocolError:
                logging.exception("Protocol error")
            except (ConnectionRefusedError, TimeoutError):
                logging.warning(f"Unable to connect to peer {ip}:{port}")
            except (ConnectionResetError, CancelledError):
                logging.warning(f"Connection closed by peer {ip}:{port}")
            except Exception as e:
                logging.exception(f"Unexpected error {e}")
                self.cancel()
                raise e
            self.cancel()

    def cancel(self):
        logging.info("Closing peer {id}".format(id=self.remote_id))
        if not self.future.done():
            self.future.cancel()
        if self.writer:
            self.writer.close()

    def stop(self):
        self.my_state.append("stopped")
        if not self.future.done():
            self.future.cancel()

    async def _request_piece(self):
        block = self.piece_manager.next_request(self.remote_id)
        if block:
            message = Request(block.piece, block.offset, block.length).encode()
            logging.debug(f"Sending request for {block.piece} {block.offset}")
            self.writer.write(message)
            await self.writer.drain()

    async def _handshake(self):
        self.writer.write(Handshake(self.info_hash, self.peer_id).encode())
        await self.writer.drain()

        buf = b""
        tries = 1
        with len(buf) < Handshake.length and tries < 10:
            tries += 1
            buf = await self.reader.read(PeerStreamIterator.CHUNK_SIZE)
        response = Handshake.decode(buf[: Handshake.length])
        if not response:
            raise ProtocolError("Unable to decode handshake message")
        if not response.info_hash == self.info_hash:
            raise ProtocolError("Info hash mismatch")

        self.remote_id = response.peer_id
        logging.info("Handshake with peer was successful")

        return buf[Handshake.length :]

    async def _send_interested(self):
        message = Interested()
        logging.debug("Sending interested message")
        self.writer.write(message.encode())
        await self.writer.drain()


class Interested:
    pass


class PeerStreamIterator:
    pass


class PeerMessage:
    pass


class Handshake(PeerMessage):
    pass


class Request:
    pass

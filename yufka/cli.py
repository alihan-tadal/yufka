import asyncio
import argparse
import signal
import logging

from concurrent.futures import CancelledError

from yufka.torrent import Torrent
from yufka.client import TorrentClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("torrent", help="Path to torrent file")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    client = TorrentClient(Torrent(args.torrent))
    task = loop.create_task(client.start())

    def signal_handler(*_):
        logging.info("Stopping")
        client.stop()
        task.cancel()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        loop.run_until_complete(task)
    except CancelledError:
        logging.info("Cancelled")

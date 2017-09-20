import json
import logging

def sendSignal(config, socket, signal):
    '''Optimistically send the signal to the Discord Bot.
    Using a UDP socket to reduce overhead.
    It is intended that both bots be hosted on the same machine, so error checking is unnessecary
    '''

    addr = config.get("discordAddress", "localhost")
    port = int(config.get("discordPort", 12345))

    bytesSent = socket.sendto(bytes(json.dumps(signal), "utf-8"), (addr, port))
    logging.info("Sent %d bytes to %s:%d", bytesSent, addr, port)

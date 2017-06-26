#!/usr/bin/python3

from multiprocessing import Process, Pipe
import os
import signal

import praw

from src.bot import listenForComments, listenForPosts
from src import config
from src.save.ImportExportHelper import loadOrGenerateConfig, importData
from src.save import Logger

def main():
    print("PictureGame Bot by Provium")
    loadOrGenerateConfig()

    reddit = praw.Reddit(config.getKey("scriptName"))
    subreddit = reddit.subreddit(config.getKey("subredditName"))

    roundNumber, roundId, currentHost, earliestTime = importData(subreddit)

    # TODO: This will need revisiting on the API branch once this merges
    # ApiConnector.login(state)

    # cts = comment process -> submission process
    # stc = submission process -> comment.process
    ctsRecv, ctsSend = Pipe(duplex = False)
    stcRecv, stcSend = Pipe(duplex = False)

    processes = [
        Process(target = listenForPosts, args = (
            ctsRecv, stcSend, roundNumber, roundId, currentHost, earliestTime)),
        Process(target = listenForComments, args = (
            stcRecv, ctsSend, roundId, roundNumber, currentHost)),
    ]

    for process in processes:
        process.start()

    try:
        # Parent process is just going to sit and wait for a ctrl+c
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        Logger.log("Starting to kill child processes", 'd')
        for process in processes:
            os.kill(process.pid, signal.SIGINT)

        os.wait()
        Logger.log("Exitting", 'd')
        return


if __name__ == "__main__":
    main()

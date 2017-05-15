from time import sleep

import config
from const import *
from actions.Retry import retry

@retry
def archiveModMail(reddit):
    conversations = reddit.get(CONVS_URL)["conversations"]

    for convId in conversations:
        conv = conversations[convId]
        if conv["subject"] == "you are an approved submitter" and \
                len(conv["authors"]) == 1 and conv["authors"][0]["name"].lower() == config.getKey("botName"):
            reddit.post(ARCHIVE_URL.format(convId))
            return

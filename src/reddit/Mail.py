from time import sleep

from const import *

def archiveModMail(reddit):
    conversations = reddit.get(CONVS_URL)["conversations"]
    sleep(2)

    for convId in conversations:
        conv = conversations[convId]
        if conv["subject"] == "you are an approved submitter" and \
                len(conv["authors"]) == 1 and conv["authors"][0]["name"] == BOT_NAME:
            reddit.post(ARCHIVE_URL.format(convId))
            sleep(2)

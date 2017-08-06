from ..const import CONVS_URL, ARCHIVE_URL
from ..actions.Retry import retry

@retry
def archiveModMail(reddit, botName):
    conversations = reddit.get(CONVS_URL)["conversations"]

    for convId in conversations:
        conv = conversations[convId]
        if conv["subject"] == "you are an approved submitter" and \
            len(conv["authors"]) == 1 and \
            conv["authors"][0]["name"].lower() == botName:
            reddit.post(ARCHIVE_URL.format(convId))
            return

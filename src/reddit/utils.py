'''Miscellaneous utility functions to be used with the retry decorator'''

from threading import Thread

from ..actions.Retry import retry
from .Mail import archiveModMail


@retry
def addContributor(reddit, subreddit, redditor):
    subreddit.contributor.add(redditor)
    Thread(target = archiveModMail, args = (reddit, )).start()


@retry
def removeContributor(subreddit, redditor):
    subreddit.contributor.remove(redditor)


@retry
def sendMessage(redditor, subject, message):
    redditor.message(subject, message)


@retry
def distinguishComment(comment, sticky = False):
    comment.mod.distinguish(sticky = sticky)


@retry
def commentReply(submissionOrComment, reply, sticky = False):
    replyComment = submissionOrComment.reply(reply)
    distinguishComment(replyComment, sticky)
    return replyComment


@retry
def getPostAuthorName(submission):
    return submission.author.name


@retry
def deleteComment(comment):
    comment.delete()


@retry
def removeThread(submission, lock = False):
    if lock:
        submission.mod.lock()
    submission.mod.remove()


@retry
def selectFlair(submission, flair):
    submission.flair.select(flair)


@retry
def getCreationTime(submissionOrComment):
    return submissionOrComment.created_utc


@retry
def editWiki(wiki, page, content):
    wiki[page].edit(content)

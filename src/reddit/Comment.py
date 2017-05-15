import config
from const import *

from actions.Retry import retry
from reddit import utils

@retry
def validate(state, comment):
    '''Check that a comment is a valid +correct'''

    # Do some easy checks before we query Reddit
    if not CORRECT_PATTERN.search(comment.body):
        return False

    if comment.is_root:
        return False

    if comment.author is None or comment.banned_by is not None:
        return False

    receivingComment = comment.parent()

    if receivingComment.author is None or receivingComment.banned_by is not None:
        return False

    correcter = comment.author.name
    receiver = receivingComment.author.name

    if receiver.lower() in DISALLOWED_NAMES.union({state.currentHost.lower(), config.getKey("botName")}):
        return False

    return correcter in state.mods.union({state.currentHost}) and \
            (receiver != correcter or correcter in state.mods)


@retry
def postSticky(winningComment, roundWinner):
    roundSubmission = winningComment.submission
    commentLink = COMMENT_URL.format(postId = roundSubmission.id, commentId = winningComment.id)
    roundAnswer = winningComment.body

    answerParts = [part.strip() for part in roundAnswer.split('\n')]
    spoileredAnswer = "   \n".join(["[{}](/spoiler)".format(part) for part in answerParts if part != ""])

    utils.commentReply(roundSubmission, 
            ROUND_OVER_STICKY.format(winnerName = roundWinner, spoileredAnswer = spoileredAnswer, commentLink = commentLink),
            sticky = not roundHasSticky(roundSubmission))


@retry
def roundHasSticky(submission):
    submission.comments.replace_more(limit = 0)
    for comment in submission.comments.list():
        if comment.stickied:
            return True
    return False

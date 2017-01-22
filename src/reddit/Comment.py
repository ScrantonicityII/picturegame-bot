from const import *

def validate(state, comment):
    '''Check that the comment meets the following conditions:
    - contains the string `+correct`
    - is posted by either the current host or a mod
    - is not a top-level comment
    - the person being +corrected is not any of the bots or the current host
    - the person giving the +correct is not the same person receiving it, unless that person is a mod
    '''

    receivingComment = comment.parent()

    if comment.author is None or receivingComment.author is None:
        return False # ignore deleted comments

    correcter = comment.author.name
    receiver = receivingComment.author.name

    return CORRECT_PATTERN.search(comment.body) and \
            correcter in state.mods.union({state.currentHost}) and \
            not comment.is_root and \
            receiver not in DISALLOWED_NAMES.union({state.currentHost, state.config["botName"]}) and \
            (receiver != correcter or correcter in state.mods)


def postSticky(state, winningComment):
    roundWinner = winningComment.author.name
    roundSubmission = winningComment.submission
    commentLink = COMMENT_URL.format(postId = state.roundId, commentId = winningComment.id)
    roundAnswer = winningComment.body
    stickyReply = roundSubmission.reply(ROUND_OVER_STICKY.format(winnerName = roundWinner, roundAnswer = roundAnswer, commentLink = commentLink))
    stickyReply.mod.distinguish(sticky = not roundHasSticky(roundSubmission))


def roundHasSticky(submission):
    submission.comments.replace_more(limit = 0)
    for comment in submission.comments.list():
        if comment.stickied:
            return True
    return False

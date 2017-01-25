from const import *

def validate(state, comment):
    '''Check that the comment meets the following conditions:
    - contains the string `+correct`
    - is posted by either the current host or a mod
    - is not a top-level comment
    - the receiving comment has not been deleted or removed
    - the person being +corrected is not any of the bots or the current host
    - the person giving the +correct is not the same person receiving it, unless that person is a mod
    '''

    receivingComment = comment.parent()

    if comment.author is None or receivingComment.author is None:
        return False # ignore deleted comments

    correcter = comment.author.name
    receiver = receivingComment.author

    return CORRECT_PATTERN.search(comment.body) and \
            correcter in state.mods.union({state.currentHost}) and \
            not comment.is_root and \
            receivingComment.banned_by is None and receiver is not None and \
            receiver.name not in DISALLOWED_NAMES.union({state.currentHost, state.config["botName"]}) and \
            (receiver.name != correcter or correcter in state.mods)


def postSticky(state, winningComment):
    roundWinner = winningComment.author.name
    roundSubmission = winningComment.submission
    commentLink = COMMENT_URL.format(postId = state.roundId, commentId = winningComment.id)
    roundAnswer = winningComment.body

    spoileredAnswer = "\n\n".join(["[{}](/spoiler)".format(part) for part in roundAnswer.split("\n\n")])

    stickyReply = roundSubmission.reply(ROUND_OVER_STICKY.format(winnerName = roundWinner, spoileredAnswer = spoileredAnswer, commentLink = commentLink))
    stickyReply.mod.distinguish(sticky = not roundHasSticky(roundSubmission))


def roundHasSticky(submission):
    submission.comments.replace_more(limit = 0)
    for comment in submission.comments.list():
        if comment.stickied:
            return True
    return False

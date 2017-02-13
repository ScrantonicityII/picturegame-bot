from const import *

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

    if receiver in DISALLOWED_NAMES.union({state.currentHost, state.config["botName"]}):
        return False

    if state.currentHost == "Provium" and "roundWinner" in state.instance and state.roundWinner["wins"] == 100 and receiver == correcter:
        return True

    return correcter in state.mods.union({state.currentHost}) and \
            (receiver != correcter or correcter in state.mods)


def postSticky(state, winningComment):
    roundWinner = winningComment.author.name
    roundSubmission = winningComment.submission
    commentLink = COMMENT_URL.format(postId = state.roundId, commentId = winningComment.id)
    roundAnswer = winningComment.body

    answerParts = [part.strip() for part in roundAnswer.split('\n')]
    spoileredAnswer = "   \n".join(["[{}](/spoiler)".format(part) for part in answerParts if part != ""])

    stickyReply = roundSubmission.reply(ROUND_OVER_STICKY.format(winnerName = roundWinner, spoileredAnswer = spoileredAnswer, commentLink = commentLink))
    stickyReply.mod.distinguish(sticky = not roundHasSticky(roundSubmission))


def roundHasSticky(submission):
    submission.comments.replace_more(limit = 0)
    for comment in submission.comments.list():
        if comment.stickied:
            return True
    return False

from const import *

def validate(state, comment):
    return CORRECT_PATTERN.match(comment.body) and \
            comment.submission.id == state.roundId and \
            comment.author.name in state.mods.union({state.currentHost}) and \
            not comment.is_root and \
            comment.parent().author.name not in DISALLOWED_NAMES.union({comment.author.name, state.currentHost})

def postSticky(state, winningComment):
    roundWinner = winningComment.author.name
    commentLink = COMMENT_URL.format(postId = state.roundId, commentId = winningComment.id)
    roundAnswer = winningComment.body
    stickyReply = winningComment.submission.reply(ROUND_OVER_STICKY.format(winnerName = roundWinner, roundAnswer = roundAnswer, commentLink = commentLink))
    stickyReply.mod.distinguish(sticky=True)

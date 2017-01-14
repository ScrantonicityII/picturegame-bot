from const import *

def validate(state, comment):
    '''Check that the comment meets the following conditions:
    - contains the string `+correct`
    - is a comment on the current round
    - is posted by either the current host or a mod
    - is not a top-level comment
    - the person being +corrected is not any of the bots, the current host, or the person giving the +correct (who may not be the host)
    '''

    return CORRECT_PATTERN.match(comment.body) and \
            comment.submission.id == state.roundId and \
            comment.author.name in state.mods.union({state.currentHost}) and \
            not comment.is_root and \
            comment.parent().author.name not in DISALLOWED_NAMES.union({comment.author.name, state.currentHost, state.config["botName"]})

def postSticky(state, winningComment):
    roundWinner = winningComment.author.name
    commentLink = COMMENT_URL.format(postId = state.roundId, commentId = winningComment.id)
    roundAnswer = winningComment.body
    stickyReply = winningComment.submission.reply(ROUND_OVER_STICKY.format(winnerName = roundWinner, roundAnswer = roundAnswer, commentLink = commentLink))
    stickyReply.mod.distinguish(sticky=True)

import re
from const import TITLE_PATTERN, REJECTION_COMMENT


def setFlair(submission, flair):
    flairs = submission.flair.choices()
    correctFlair = next(f for f in flairs if f["flair_text"] == flair)
    flairId = correctFlair["flair_template_id"]
    submission.flair.select(flairId)


def validate(state, submission):
    '''Check that the post meets the following conditions:
    - was posted after the previous round was won
    - is not a self post (rounds are always links, self posts must be mod posts)
    - is not locked
    '''
    return submission.created_utc > state.roundWonTime and \
            not submission.is_self and \
            not submission.locked


def rejectIfInvalid(state, submission):
    '''Lock and comment on a new round if it is titled incorrectly'''

    correctTitlePattern = re.compile("^\[Round {}\]".format(state.roundNumber), re.I)

    if not correctTitlePattern.match(submission.title):
        titleRemainder = TITLE_PATTERN.sub("", submission.title)
        correctTitle = "[Round {}] {}".format(state.roundNumber, titleRemainder)

        rejectionReply = submission.reply(REJECTION_COMMENT.format(correctTitle = correctTitle))
        rejectionReply.mod.distinguish(sticky = True)

        submission.mod.lock()
        state.subreddit.mod.remove(submission)
        return False

    return True

import logging
import re

from .. import config
from ..const import TITLE_CORRECTION_PATTERN, REJECTION_COMMENT, \
    DUPLICATE_ROUND_REPLY, ABANDONED_FLAIRS

from ..actions.Retry import retry
from . import utils

flairChoiceCache = None


@retry
def setFlair(submission, flair):
    if flairChoiceCache is None:
        getFlairChoices(submission)

    flairId = flairChoiceCache[flair]
    submission.flair.select(flairId)


@retry
def getFlairChoices(submission):
    global flairChoiceCache

    flairs = submission.flair.choices()
    flairChoices = {}
    for flair in flairs:
        flairChoices[flair["flair_text"]] = flair["flair_template_id"]

    flairChoiceCache = flairChoices


@retry
def validate(state, submission):
    '''Check that the post meets the following conditions:
    - was posted after the previous round was won
    - is not a self post (rounds are always links, self posts must be mod posts)
    - is not locked
    - is not deleted/removed
    - is not already flaired
    '''
    return submission.created_utc > state.roundWonTime and \
            not submission.is_self and \
            not submission.locked and \
            submission.link_flair_text is None and \
            submission.author is not None and submission.banned_by is None


@retry
def rejectIfInvalid(state, submission):
    '''Lock and comment on a new round if it is titled incorrectly'''

    correctTitlePattern = re.compile(r"^\[Round {}\]".format(state.roundNumber), re.I)
    roundTitle = submission.title

    if not correctTitlePattern.match(roundTitle):
        titleRemainder = TITLE_CORRECTION_PATTERN.sub("", roundTitle)
        correctTitle = "[Round {}] {}".format(state.roundNumber, titleRemainder)

        utils.commentReply(submission,
            REJECTION_COMMENT.format(
                correctTitle = correctTitle, subredditName = config.getKey("subredditName")),
            sticky = True)

        utils.removeThread(submission, lock = True)
        return False

    return True


@retry
def checkForStrays(state, currentSubmission):
    '''Comment on posts that are made while a round is active'''

    for submission in state.subreddit.new(limit=5):
        if submission.created_utc <= currentSubmission.created_utc or \
            submission.id in state.seenPosts:
            break
        if not submission.is_self:
            reply = utils.commentReply(submission, DUPLICATE_ROUND_REPLY.format(
                roundUrl = currentSubmission.permalink))
            state.commentedRoundIds[submission.id] = reply
        state.seenPosts.add(submission.id)


@retry
def deleteExtraPosts(reddit, commentedRoundIds):
    '''Delete any posts that were made during the previous round. Ignore self (mod) posts'''

    for postId in commentedRoundIds:
        submission = reddit.submission(postId)
        utils.removeThread(submission)


@retry
def checkDeleted(state, submission):
    '''Check if the current round has been deleted or removed
    Return to listening for rounds if it has'''

    if submission.author is None or submission.banned_by is not None:
        logging.info("Round deleted, going back to listening for rounds")

        utils.selectFlair(submission, None)
        state.setState({ "unsolved": False })
        return True

    return False


@retry
def checkAbandoned(state, submission):
    '''Check if the current round has been flaired abandoned or terminated,
    or manually flaired over.
    Bump up the round number and return to listening for rounds if it has'''

    if submission.link_flair_text in ABANDONED_FLAIRS:
        logging.info("Round abandoned, cleaning up")

        utils.removeContributor(state.subreddit, state.currentHost)
        deleteExtraPosts(state.reddit, state.commentedRoundIds)

        submittedTime = utils.getCreationTime(submission)
        state.setState({
            "unsolved": False,
            "roundNumber": state.roundNumber + 1,
            "roundWonTime": submittedTime
        })
        return True

    return False

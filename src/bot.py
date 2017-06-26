import json
import signal
from threading import Thread
from time import sleep, time

import praw

from . import config
from .const import WINNER_SUBJECT, WINNER_PM, OVER_FLAIR, PLUSCORRECT_REPLY, UNSOLVED_FLAIR, \
    NEW_ROUND_COMMENT, VERSION_URL, NEW_VERSION_SUBJECT, NEW_VERSION_PM, DUPLICATE_ROUND_REPLY

from .actions.Retry import retry

from .api import ApiConnector

from .reddit import Comment, Post, User, utils, Wiki

from .save import ImportExportHelper, Logger

MOD_REFRESH_TIME = 86400 # Refresh the mod list daily


def handleSignal(signum, frame):
    raise OSError("Caught a signal: {}".format(signum))


@retry
def getMods(subreddit):
    return set(map(lambda mod: mod.name, subreddit.moderator()))


def listenForComments(inPipe, outPipe, roundId, roundNumber, currentHost):
    signal.signal(signal.SIGINT, handleSignal)

    def listenOnPipe():
        nonlocal roundId, roundNumber, currentHost
        while True:
            data = json.loads(inPipe.recv())
            roundId = data["roundId"]
            roundNumber = data["roundNumber"]
            currentHost = data["currentHost"]
            Logger.log("listenForComments: got new round, id: {} number: {} host: {}".format(
                roundId, roundNumber, currentHost), 'i')

    Thread(target = listenOnPipe, daemon = True).start()

    reddit = praw.Reddit(config.getKey("scriptName"))
    subreddit = reddit.subreddit(config.getKey("subredditName"))

    modTimer = time()
    mods = getMods(subreddit)

    try:
        for comment in subreddit.stream.comments():
            if roundId is None:
                # Ignore the comment if there's no round going
                continue

            currentTime = time()
            if modTimer + MOD_REFRESH_TIME < currentTime:
                mods = getMods(subreddit)
                modTimer = currentTime

            if Comment.validate(comment, roundId, currentHost, mods):
                winner = onRoundOver(comment, reddit, subreddit, roundNumber, currentHost)
                roundId = None
                outPipe.send(winner)
    except OSError:
        Logger.log("listenForComments: exitting", 'd')
        return


@retry
def onRoundOver(comment, reddit, subreddit, roundNumber, currentHost):
    winningComment = comment.parent()
    roundWinner = winningComment.author
    Logger.log("Round {} won by {}".format(roundNumber, roundWinner.name))

    Thread(target = roundOverBackgroundTasks,
        args = (subreddit, currentHost, winningComment, roundWinner.name)
    ).start()

    groupId = Logger.log("Starting main thread tasks", 'd', discard = False)

    # TODO
    # ApiConnector.tryRequest(state, ApiConnector.put, roundNumber, winningComment)

    utils.addContributor(reddit, subreddit, roundWinner.name)
    utils.sendMessage(roundWinner,
        WINNER_SUBJECT,
        WINNER_PM.format(
            roundNum = roundNumber + 1, subredditName = config.getKey("subredditName")))

    awardWin(subreddit, roundWinner.name, roundNumber)

    User.setFlair(subreddit, roundWinner, winningComment)

    Post.setFlair(comment.submission, OVER_FLAIR)

    Logger.log("Main thread tasks finished", 'd', groupId)
    return roundWinner.name


def awardWin(subreddit, username, roundNumber):
    leaderboard = Wiki.scrapeLeaderboard(subreddit)

    rounds = []
    if username in leaderboard:
        rounds = leaderboard[username]["rounds"] + [roundNumber]
    else:
        rounds = [roundNumber]

    leaderboard[username] = {
        "wins": len(rounds),
        "rounds": rounds,
    }

    ImportExportHelper.exportLeaderboard(subreddit, leaderboard)


def roundOverBackgroundTasks(subreddit, currentHost, winningComment, winnerName):
    '''Run some of the round-over tasks that don't need to be in sequence in a different thread'''

    groupId = Logger.log("Starting background tasks", 'd', discard = False)
    utils.commentReply(winningComment, PLUSCORRECT_REPLY)

    utils.removeContributor(subreddit, currentHost)

    Comment.postSticky(winningComment, winnerName)
    Logger.log("Background tasks finished", 'd', groupId)


def listenForPosts(inPipe, outPipe, roundNumber, roundId, currentHost, earliestTime):
    '''Post listener process
     - Checks for new threads and determines if a new thread results in the starting of a round
     - Notifies the comment listener process if a new round starts
     - Is notified by the comment listener if the round ends
     - Is notified by the status checker if the round is deleted or abandoned
     '''

    signal.signal(signal.SIGINT, handleSignal)

    def listenOnPipe():
        nonlocal roundId, roundNumber, currentHost, reddit, commentedRoundIds
        while True:
            currentHost = inPipe.recv()
            roundNumber += 1
            roundId = None # Round ended
            Logger.log("listenForPosts: got new prospective host, {}".format(currentHost), 'i')
            Post.deleteExtraPosts(reddit, commentedRoundIds)
            commentedRoundIds = {}

    Thread(target = listenOnPipe, daemon = True).start()

    reddit = praw.Reddit(config.getKey("scriptName"))
    subreddit = reddit.subreddit(config.getKey("subredditName"))
    commentedRoundIds = {}

    # TODO: status checker process/pipe

    try:
        for submission in subreddit.stream.submissions():
            if submission.created_utc <= earliestTime or \
                submission.is_self:
                continue

            Logger.log("Found new post, id: {}".format(submission.id), 'd')
            if roundId is None:
                if Post.validate(submission) and Post.rejectIfInvalid(submission, roundNumber):
                    currentHost = onNewRoundPosted(submission, subreddit, roundNumber, currentHost)
                    roundId = submission.id
                    if submission.id in commentedRoundIds:
                        utils.deleteComment(commentedRoundIds[submission.id])
                    outPipe.send(json.dumps({
                        "currentHost": currentHost,
                        "roundId": roundId,
                        "roundNumber": roundNumber,
                    }))
            else:
                # Round already going, comment on stray post and mark for deletion
                reply = utils.commentReply(submission, DUPLICATE_ROUND_REPLY.format(
                    roundId = roundId))
                commentedRoundIds[submission.id] = reply
    except OSError:
        Logger.log("listenForPosts: exitting", 'd')
        return


@retry
def onNewRoundPosted(submission, subreddit, roundNumber, currentHost):
    # TODO
    # ApiConnector.tryRequest(state, ApiConnector.post, roundNumber, submission)

    postAuthor = utils.getPostAuthorName(submission)

    Post.setFlair(submission, UNSOLVED_FLAIR)

    if postAuthor != currentHost: # de-perm the original +CP if someone else took over
        utils.removeContributor(subreddit, currentHost)

    utils.commentReply(submission,
        NEW_ROUND_COMMENT.format(
            hostName = postAuthor, subredditName = config.getKey("subredditName")))

    return postAuthor

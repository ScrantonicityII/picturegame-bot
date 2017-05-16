#!/usr/bin/python3

from threading import Thread
from time import sleep
import urllib.request

import praw

from . import config
from .const import WINNER_SUBJECT, WINNER_PM, OVER_FLAIR, PLUSCORRECT_REPLY, UNSOLVED_FLAIR, \
    NEW_ROUND_COMMENT, VERSION_URL, NEW_VERSION_SUBJECT, NEW_VERSION_PM

from .actions.Retry import retry

from .api import ApiConnector

from .reddit import Comment, Post, User, utils

from .save import Logger
from .save.ImportExportHelper import loadOrGenerateConfig
from .save.State import State


@retry
def listenForComments(state):
    Logger.log("Listening for +correct on round {}...".format(state.roundNumber))

    forestState = {}

    while True:
        currentSubmission = state.reddit.submission(id = state.roundId)

        Post.checkForStrays(state, currentSubmission)

        if Post.checkDeleted(state, currentSubmission):
            return

        if Post.checkAbandoned(state, currentSubmission):
            return

        # Can use `limit = None` to unpack the entire tree in one line,
        # but this is very inefficient in large threads
        leftovers = currentSubmission.comments.replace_more(limit = 0)

        commentSet = {comment for comment in currentSubmission.comments.list() \
                if comment.id not in state.seenComments}
        state.seenComments = state.seenComments.union({comment.id for comment in commentSet})

        # Traverse the `MoreComments` trees, but ignore any that have not had any more comments
        # since the last update. Unfortunately this method cannot open `continue this thread`
        # handles, so comments beyond a depth of 10 will not be seen by the bot. This still allows
        # reading of unlimited top-level comments, which is the main use-case for PG, and maintains
        # decent performance.
        while leftovers:
            commentTree = leftovers.pop()
            if forestState.get(commentTree.id, -1) < commentTree.count:
                if commentTree.id != '_':
                    forestState[commentTree.id] = commentTree.count

                for comment in commentTree.comments():
                    if isinstance(comment, praw.models.reddit.comment.Comment):
                        if comment.id not in state.seenComments:
                            state.seenComments.add(comment.id)
                            commentSet.add(comment)
                    else:
                        leftovers.append(comment)

        sortedComments = sorted(commentSet, key = lambda comment: comment.created_utc)
        for comment in sortedComments:
            if Comment.validate(state, comment):
                onRoundOver(state, comment)
                return

        sleep(10) # Wait a while before checking again to avoid doing too many requests


@retry
def onRoundOver(state, comment):
    winningComment = comment.parent()
    roundWinner = winningComment.author
    Logger.log("Round {} won by {}".format(state.roundNumber, roundWinner.name))

    Thread(target = roundOverBackgroundTasks,
        args = (state.subreddit, state.currentHost, winningComment, roundWinner.name)
    ).start()

    groupId = Logger.log("Starting main thread tasks", 'd', discard = False)

    # ApiConnector.tryRequest(state, ApiConnector.put, state.roundNumber, winningComment)

    # Delete extra posts before anything else so we don't accidentally delete the next round
    Post.deleteExtraPosts(state.reddit, state.commentedRoundIds)

    utils.addContributor(state.reddit, state.subreddit, roundWinner.name)
    utils.sendMessage(roundWinner,
        WINNER_SUBJECT,
        WINNER_PM.format(
            roundNum = state.roundNumber + 1, subredditName = config.getKey("subredditName")))

    state.awardWin(roundWinner.name, winningComment)
    state.seenComments = set()
    state.seenPosts = set()

    User.setFlair(state, roundWinner, winningComment)

    Post.setFlair(comment.submission, OVER_FLAIR)

    Logger.log("Main thread tasks finished", 'd', groupId)


def roundOverBackgroundTasks(subreddit, currentHost, winningComment, winnerName):
    '''Run some of the round-over tasks that don't need to be in sequence in a different thread'''

    groupId = Logger.log("Starting background tasks", 'd', discard = False)
    utils.commentReply(winningComment, PLUSCORRECT_REPLY)

    utils.removeContributor(subreddit, currentHost)

    Comment.postSticky(winningComment, winnerName)
    Logger.log("Background tasks finished", 'd', groupId)


@retry
def listenForPosts(state):
    Logger.log("Listening for new rounds...")

    for submission in state.subreddit.stream.submissions():
        if Post.validate(state, submission):
            if onNewRoundPosted(state, submission):
                break

@retry
def onNewRoundPosted(state, submission):
    state.updateMods()

    # ApiConnector.tryRequest(state, ApiConnector.post, state.roundNumber, submission)

    postAuthor = utils.getPostAuthorName(submission)

    if not Post.rejectIfInvalid(state, submission):
        return False

    Post.setFlair(submission, UNSOLVED_FLAIR)

    if postAuthor != state.currentHost: # de-perm the original +CP if someone else took over
        utils.removeContributor(state.subreddit, state.currentHost)

    utils.commentReply(submission,
        NEW_ROUND_COMMENT.format(
            hostName = postAuthor, subredditName = config.getKey("subredditName")))

    if submission.id in state.commentedRoundIds:
        utils.deleteComment(state.commentedRoundIds[submission.id])
    state.commentedRoundIds = {}

    newState = {
        "unsolved": True,
        "roundId": submission.id
    }
    if postAuthor != state.currentHost:
        newState["currentHost"] = postAuthor

    state.setState(newState)

    return True


@retry
def fetchLatestVersion():
    webResource = urllib.request.urlopen(VERSION_URL)
    return str(webResource.read(), "utf-8").strip()


def checkVersion(state):
    while True:
        latestVersion = fetchLatestVersion()
        if latestVersion != state.seenVersion:
            owner = state.reddit.redditor(config.getKey("ownerName"))
            utils.sendMessage(owner, NEW_VERSION_SUBJECT, NEW_VERSION_PM)
            state.seenVersion = latestVersion

        sleep(86400) # Just check every day


def main():
    print("PictureGame Bot by Provium")
    print("Press ctrl+c to exit")

    loadOrGenerateConfig()
    state = State()
    # ApiConnector.login(state)

    versionThread = Thread(target = checkVersion, args = (state,), daemon = True)
    versionThread.start()

    try:
        while True:
            if state.unsolved:
                listenForComments(state)
            else:
                listenForPosts(state)
    except KeyboardInterrupt:
        print("\nExitting...")


if __name__ == "__main__":
    main()

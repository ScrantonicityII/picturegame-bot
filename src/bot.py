import argparse
import logging
import logging.config
import os
import sys
from threading import Thread
from time import sleep

import praw

from .const import WINNER_SUBJECT, WINNER_PM, OVER_FLAIR, PLUSCORRECT_REPLY, UNSOLVED_FLAIR, \
    NEW_ROUND_COMMENT, CONFIG_FILENAME

from .actions.Retry import retry

# from .api import ApiConnector

from .discord import discord

from .reddit import Comment, Post, User, utils

from .save.State import State


@retry
def listenForComments(state):
    logging.info("Listening for +correct on round %d...", state.roundNumber)

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
    logging.info("Round %d won by %s", state.roundNumber, roundWinner.name)

    Thread(target = roundOverBackgroundTasks,
        args = (state.subreddit, state.currentHost, winningComment, roundWinner.name)
    ).start()

    logging.debug("Starting main thread tasks")

    # ApiConnector.tryRequest(state, ApiConnector.put, state.roundNumber, winningComment)

    # Delete extra posts before anything else so we don't accidentally delete the next round
    Post.deleteExtraPosts(state.reddit, state.commentedRoundIds)

    utils.addContributor(state.reddit, state.subreddit, roundWinner.name,
        state.config.getlower("botName"))
    utils.sendMessage(roundWinner,
        WINNER_SUBJECT,
        WINNER_PM.format(
            roundNum = state.roundNumber + 1, subredditName = state.config["subredditName"]))

    winCount = state.awardWin(roundWinner.name, winningComment)
    state.seenComments = set()
    state.seenPosts = set()

    User.setFlair(state, roundWinner, winningComment)

    Post.setFlair(comment.submission, OVER_FLAIR)

    discord.sendSignal(state.config, state.socket, {
        "status": "solved",
        "winner": roundWinner.name,
        "winCount": winCount,
        "commentId": winningComment.id,
    })

    logging.debug("Main thread tasks finished")


def roundOverBackgroundTasks(subreddit, currentHost, winningComment, winnerName):
    '''Run some of the round-over tasks that don't need to be in sequence in a different thread'''

    logging.debug("Starting background tasks")
    utils.commentReply(winningComment, PLUSCORRECT_REPLY)

    utils.removeContributor(subreddit, currentHost)

    Comment.postSticky(winningComment, winnerName)
    logging.debug("Background tasks finished")


@retry
def listenForPosts(state):
    logging.info("Listening for new rounds...")

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
            hostName = postAuthor, subredditName = state.config["subredditName"]))

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

    discord.sendSignal(state.config, state.socket, {
        "status": "new",
        "url": submission.url,
        "id": submission.id,
        "host": postAuthor,
        "title": submission.title,
    })

    return True


def setup():
    if not os.path.isdir('data'):
        os.mkdir('data')

    with open('VERSION') as f:
        print("PictureGame Bot {} by Provium\n------\n".format(f.read().strip()))

    parser = argparse.ArgumentParser(description="The /r/PictureGame Reddit Bot.")

    parser.add_argument("--env", type = str, required = True,
        help = "Name of the environment to use from bot.conf")
    parser.add_argument("--logConfig", type = str,
        help = "Name of the file from which to load logging config")

    args = parser.parse_args()

    valid = True

    for fileName in [args.logConfig, CONFIG_FILENAME]:
        if fileName is not None and not os.path.isfile(fileName):
            print("File not found:", fileName)
            valid = False

    if not valid:
        sys.exit()

    state = State(args)
    logging.info("Setup successful")

    return state


def main():
    state = setup()

    # ApiConnector.login(state)

    try:
        while True:
            if state.unsolved:
                listenForComments(state)
            else:
                listenForPosts(state)
    except KeyboardInterrupt:
        print("\nExitting...")

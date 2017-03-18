#!/usr/bin/python3

import praw
from threading import Thread
from time import sleep
import urllib.request

import config
from const import *

from actions.Retry import actionWithRetry 

from api import ApiConnector

from reddit import Comment, Post, Mail, User

from save import Logger
from save.ImportExportHelper import loadOrGenerateConfig
from save.State import State


def listenForComments(state):
    Logger.log("Listening for +correct on round {}...".format(state.roundNumber))

    forestState = {}

    while True:
        currentSubmission = state.reddit.submission(id = state.roundId)

        actionWithRetry(Post.checkForStrays, state, currentSubmission)
        
        if actionWithRetry(Post.checkDeleted, state, currentSubmission):
            return

        if actionWithRetry(Post.checkAbandoned, state, currentSubmission):
            return

        # Can use `limit = None` to unpack the entire tree in one line, but this is very inefficient in large threads
        leftovers = currentSubmission.comments.replace_more(limit = 0)

        commentSet = {comment for comment in currentSubmission.comments.list() if comment.id not in state.seenComments}
        state.seenComments = state.seenComments.union({comment.id for comment in commentSet})

        # Traverse the `MoreComments` trees, but ignore any that have not had any more comments since the last update
        # Unfortunately this method cannot open `continue this thread` handles, so comments beyond a depth of 10 will not be seen by the bot
        # This still allows reading of unlimited top-level comments, which is the main use-case for PG, and maintains decent performance
        while len(leftovers):
            commentTree = leftovers.pop()
            if forestState.get(commentTree.id, -1) < commentTree.count:
                if commentTree.id != '_':
                    forestState[commentTree.id] = commentTree.count

                for comment in commentTree.comments():
                    if type(comment) == praw.models.reddit.comment.Comment:
                        if comment.id not in state.seenComments:
                            state.seenComments.add(comment.id)
                            commentSet.add(comment)
                    else:
                        leftovers.append(comment)

        sortedComments = sorted(commentSet, key = lambda comment: comment.created_utc)
        for comment in sortedComments:
            if actionWithRetry(Comment.validate, state, comment):
                actionWithRetry(onRoundOver, state, comment)
                return

        sleep(10) # Wait a while before checking again to avoid doing too many requests


def onRoundOver(state, comment):
    winningComment = comment.parent()
    roundWinner = winningComment.author
    Logger.log("Round {} won by {}".format(state.roundNumber, roundWinner.name))

    # actionWithRetry(ApiConnector.tryRequest, state, ApiConnector.put, state.roundNumber, winningComment)

    actionWithRetry(Post.deleteExtraPosts, state, comment.submission) # delete extra posts before anything else so we don't accidentally delete the next round

    replyComment = actionWithRetry(winningComment.reply, PLUSCORRECT_REPLY)
    actionWithRetry(replyComment.mod.distinguish)

    actionWithRetry(state.subreddit.contributor.remove, state.currentHost)
    actionWithRetry(state.subreddit.contributor.add, roundWinner.name)
    actionWithRetry(Mail.archiveModMail, state)

    actionWithRetry(roundWinner.message, WINNER_SUBJECT, WINNER_PM.format(roundNum = state.roundNumber + 1, subredditName = config.getKey("subredditName")))

    actionWithRetry(Comment.postSticky, state, winningComment)

    state.awardWin(roundWinner.name, winningComment)
    state.seenComments = set()
    state.seenPosts = set()

    actionWithRetry(User.setFlair, state, roundWinner, winningComment)
    actionWithRetry(Post.setFlair, comment.submission, OVER_FLAIR)


def listenForPosts(state):
    Logger.log("Listening for new rounds...")

    for submission in state.subreddit.stream.submissions():
        if actionWithRetry(Post.validate, state, submission):
            if actionWithRetry(onNewRoundPosted, state, submission):
                break


def onNewRoundPosted(state, submission):
    actionWithRetry(state.updateMods)

    # actionWithRetry(ApiConnector.tryRequest, state, ApiConnector.post, state.roundNumber, submission)

    postAuthor = actionWithRetry(lambda s: s.author.name, submission)
    postId = actionWithRetry(lambda s: s.id, submission)

    if not actionWithRetry(Post.rejectIfInvalid, state, submission):
        return False

    actionWithRetry(Post.setFlair, submission, UNSOLVED_FLAIR)

    if postAuthor != state.currentHost: # de-perm the original +CP if someone else took over
        actionWithRetry(state.subreddit.contributor.remove, state.currentHost)

    newRoundReply = actionWithRetry(submission.reply, NEW_ROUND_COMMENT.format(hostName = postAuthor, subredditName = config.getKey("subredditName")))
    newRoundReply.mod.distinguish()

    if postId in state.commentedRoundIds:
        actionWithRetry(state.commentedRoundIds[postId].delete)
    state.commentedRoundIds = {}

    newState = {
            "unsolved": True,
            "roundId": postId
            }
    if postAuthor != state.currentHost:
        newState["currentHost"] = postAuthor

    state.setState(newState)

    return True


def fetchLatestVersion():
    webResource = urllib.request.urlopen(VERSION_URL)
    return str(webResource.read(), "utf-8").strip()


def checkVersion(state):
    while True:
        latestVersion = actionWithRetry(fetchLatestVersion)
        if latestVersion != state.seenVersion:
            owner = state.reddit.redditor(config.getKey("ownerName"))
            actionWithRetry(owner.message, NEW_VERSION_SUBJECT, NEW_VERSION_PM)
            state.seenVersion = latestVersion

        sleep(86400) # Just check every day


def main():
    print("PictureGame Bot by Provium")
    print("Press ctrl+c to exit")
    
    loadOrGenerateConfig()
    state = State()
    # ApiConnector.login(state)

    versionThread = Thread(target = checkVersion, args = (state,))
    versionThread.start()

    try:
        while True:
            if state.unsolved:
                actionWithRetry(listenForComments, state)
            else:
                actionWithRetry(listenForPosts, state)
    except KeyboardInterrupt:
        print("\nExitting...")
    

if __name__ == "__main__":
    main()

#!/usr/bin/python3

from time import sleep

from save.State import State
from reddit import Comment, Post, Mail, User
from const import *
from save import Logger
from actions.Retry import actionWithRetry 


def listenForComments(state):
    Logger.log("Listening for +correct on round {}...".format(state.roundNumber))

    while True:
        currentSubmission = state.reddit.submission(id = state.roundId)

        actionWithRetry(Post.checkForStrays, state, currentSubmission)
        
        if actionWithRetry(Post.checkDeleted, state, currentSubmission):
            return

        if actionWithRetry(Post.checkAbandoned, state, currentSubmission):
            return

        currentSubmission.comments.replace_more(limit = 0)
        commentList = currentSubmission.comments.list()
        sortedComments = sorted(commentList, key = lambda comment: comment.created_utc)
        for comment in sortedComments:
            if comment.id in state.seenComments:
                continue

            state.seenComments.add(comment.id)
            if actionWithRetry(Comment.validate, state, comment):
                actionWithRetry(onRoundOver, state, comment)
                return

        sleep(10) # Wait a while before checking again to avoid doing too many requests


def onRoundOver(state, comment):
    winningComment = comment.parent()
    roundWinner = winningComment.author
    Logger.log("Round {} won by {}".format(state.roundNumber, roundWinner.name))

    actionWithRetry(Post.deleteExtraPosts, state, comment.submission) # delete extra posts before anything else so we don't accidentally delete the next round

    replyComment = actionWithRetry(winningComment.reply, PLUSCORRECT_REPLY)
    actionWithRetry(replyComment.mod.distinguish)

    actionWithRetry(state.subreddit.contributor.remove, state.currentHost)
    actionWithRetry(state.subreddit.contributor.add, roundWinner.name)
    actionWithRetry(Mail.archiveModMail, state)

    actionWithRetry(roundWinner.message, WINNER_SUBJECT, WINNER_PM.format(roundNum = state.roundNumber + 1, subredditName = state.config["subredditName"]))

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

    postAuthor = actionWithRetry(lambda s: s.author.name, submission)
    postId = actionWithRetry(lambda s: s.id, submission)

    if not actionWithRetry(Post.rejectIfInvalid, state, submission):
        return False

    actionWithRetry(Post.setFlair, submission, UNSOLVED_FLAIR)

    if postAuthor != state.currentHost: # de-perm the original +CP if someone else took over
        actionWithRetry(state.subreddit.contributor.remove, state.currentHost)

    newRoundReply = actionWithRetry(submission.reply, NEW_ROUND_COMMENT.format(hostName = postAuthor, subredditName = state.config["subredditName"]))
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


def main():
    print("PictureGame Bot by Provium")
    print("Press ctrl+c to exit")
    state = State()

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

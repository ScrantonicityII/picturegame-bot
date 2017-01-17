#!/usr/bin/python3

from time import sleep

from save.State import State
from reddit import Comment, Post, Mail, User
from const import *
from save import Logger


def listenForComments(state):
    Logger.log("Listening for +correct on round {}...".format(state.roundNumber))

    while True:
        currentSubmission = state.reddit.submission(id = state.roundId)

        currentSubmission.comments.replace_more(limit = 0)
        commentList = currentSubmission.comments.list()
        sortedComments = sorted(commentList, key = lambda comment: comment.created_utc)
        for comment in sortedComments:
            if comment.id in state.seenComments:
                continue

            state.seenComments.add(comment.id)
            if Comment.validate(state, comment):
                onRoundOver(state, comment)
                return

        sleep(10) # Wait a while before checking again to avoid doing too many requests


def onRoundOver(state, comment):
    winningComment = comment.parent()
    roundWinner = winningComment.author
    Logger.log("Round {} won by {}".format(state.roundNumber, roundWinner.name))

    Post.deleteExtraPosts(state, comment.submission) # delete extra posts before anything else so we don't accidentally delete the next round

    replyComment = winningComment.reply(PLUSCORRECT_REPLY)
    replyComment.mod.distinguish()

    Post.setFlair(comment.submission, OVER_FLAIR)

    state.awardWin(roundWinner.name, winningComment)
    state.seenComments = set()

    state.subreddit.contributor.add(roundWinner.name)
    Mail.archiveModMail(state)

    roundWinner.message(WINNER_SUBJECT, WINNER_PM.format(roundNum = state.roundNumber, subredditName = state.config["subredditName"]))
    User.setFlair(state, roundWinner, winningComment)

    Comment.postSticky(state, winningComment)


def listenForPosts(state):
    Logger.log("Listening for new rounds...")

    for submission in state.subreddit.stream.submissions():
        if Post.validate(state, submission):
            if onNewRoundPosted(state, submission):
                break


def onNewRoundPosted(state, submission):
    if not Post.rejectIfInvalid(state, submission):
        return False

    Post.setFlair(submission, UNSOLVED_FLAIR)

    state.subreddit.contributor.remove(submission.author)
    if submission.author.name != state.currentHost: # de-perm the original +CP if someone else took over
        state.subreddit.contributor.remove(state.currentHost)

    newRoundReply = submission.reply(NEW_ROUND_COMMENT.format(hostName = submission.author.name, subredditName = state.config["subredditName"]))
    newRoundReply.mod.distinguish()

    newState = {
            "unsolved": True,
            "roundId": submission.id
            }
    if submission.author.name != state.currentHost:
        newState["currentHost"] = submission.author.name

    state.setState(newState)

    return True


def main():
    print("PictureGame Bot by Provium")
    print("Press ctrl+c to exit")
    state = State()

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

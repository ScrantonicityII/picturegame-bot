#!/usr/bin/python3

from save.State import State
from reddit import Comment, Post, Mail, User
from const import *


def listenForComments(state):
    for comment in state.subreddit.stream.comments():
        if Comment.validate(state, comment):
            onRoundOver(state, comment)
            break


def onRoundOver(state, comment):
    winningComment = comment.parent()
    roundWinner = winningComment.author
    replyComment = winningComment.reply(PLUSCORRECT_REPLY)
    replyComment.mod.distinguish()
    Post.setFlair(comment.submission, OVER_FLAIR)
    state.awardWin(roundWinner.name, winningComment)
    state.subreddit.contributor.add(roundWinner.name)
    Mail.archiveModMail(state)
    roundWinner.message(WINNER_SUBJECT, WINNER_PM.format(roundNum = state.roundNumber, subredditName = state.config["subredditName"]))
    User.setFlair(state, roundWinner, winningComment)
    Comment.postSticky(state, winningComment)


def listenForPosts(state):
    for submission in state.subreddit.stream.submissions():
        continue


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

import json
from const import *
from actions.Retry import actionWithRetry


def scrapeLeaderboard(subreddit):
    wikiPageData = subreddit.wiki["leaderboard"].content_md.split('\n')[4:-1] # first four rows are headers and last row is blank
    leaderboard = {}
    for line in wikiPageData:
        rank, name, rawRounds, winCount = line.split(" | ")
        rounds = [int(round) for round in rawRounds.split(", ")]
        leaderboard[name] = {
                "wins": int(winCount),
                "rounds": rounds
                }
    return leaderboard


def exportLeaderboard(subreddit, leaderboard):

    # Sort first on most recent win, then on total win count
    # Python's sorted() is a stable sort so if two people conflict in the second sort they will maintain the ordering from the first
    firstSort = sorted(leaderboard, key = lambda name: leaderboard[name]["rounds"][-1])
    sortedNames = sorted(firstSort, key = lambda name: leaderboard[name]["wins"], reverse = True)

    outputString = LEADERBOARD_HEADER
    for (index, name) in enumerate(sortedNames):
        outputString += "{} | {} | {} | {}\n".format(
                index + 1,
                name,
                ", ".join([str(num) for num in leaderboard[name]["rounds"]]),
                leaderboard[name]["wins"]
                )

    actionWithRetry(subreddit.wiki["leaderboard"].edit, outputString)

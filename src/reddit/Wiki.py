import json


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

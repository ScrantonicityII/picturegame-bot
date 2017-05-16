import re

from ..const import LEADERBOARD_HEADER

from ..actions.Retry import retry

from . import utils

@retry
def scrapeLeaderboard(subreddit):
    # first four rows are headers and last row is blank
    wikiPageData = subreddit.wiki["leaderboard"].content_md.split('\n')[4:-1]

    leaderboard = {}
    for line in wikiPageData:
        _, name, rawRounds, _ = line.split(" | ")

        # Convoluted unpacking of round numbers
        # Instead of splitting on a delimiter, group by maximal "words" of letters and numbers,
        # and then remove anything that's not a number
        rounds = [int(re.sub(r"\D", "", rawRound)) for rawRound in \
            re.findall(r"[\w\d]+", rawRounds)]

        leaderboard[name] = {
            "wins": len(rounds),
            "rounds": rounds
        }
    return leaderboard


def exportLeaderboard(subreddit, leaderboard):

    # Sort first on most recent win, then on total win count
    # Python's sorted() is a stable sort so if two people conflict in the second sort,
    # they will maintain the ordering from the first
    firstSort = sorted(leaderboard, key = lambda name: leaderboard[name]["rounds"][-1])
    sortedNames = sorted(firstSort, key = lambda name: leaderboard[name]["wins"], reverse = True)

    outputString = LEADERBOARD_HEADER
    for (index, name) in enumerate(sortedNames):
        outputString += "{} | {} | {} | {}\n".format(
            index + 1,
            name,
            ", ".join([str(num) for num in leaderboard[name]["rounds"]]),
            leaderboard[name]["wins"])

    utils.editWiki(subreddit.wiki, "leaderboard", outputString)

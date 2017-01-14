from const import LOW_FLAIR_PATTERN, HIGH_FLAIR_PATTERN

def setFlair(state, user, comment):
    numWins = state.leaderboard[user.name]["wins"]
    oldFlair = comment.author_flair_text or ""
    flairText = ""
    customFlair = ""
    if (numWins <= 8 and not LOW_FLAIR_PATTERN.match(oldFlair)) or \
            (numWins > 8 and not HIGH_FLAIR_PATTERN.match(oldFlair)):
        print(oldFlair, LOW_FLAIR_PATTERN.match(oldFlair))
        return # don't update flair if it doesn't match the given format

    if numWins < 8:
        rounds = state.leaderboard[user.name]["rounds"]
        flairText = "Round " + ", ".join([str(roundNum) for roundNum in rounds])
        customFlair = LOW_FLAIR_PATTERN.sub("", oldFlair)
    else:
        flairText = "{} wins".format(numWins)
        customFlair = HIGH_FLAIR_PATTERN.sub("", oldFlair)

    newFlair = flairText + customFlair
    state.subreddit.flair.set(user, text = newFlair)

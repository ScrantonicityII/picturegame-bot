from ..const import LOW_FLAIR_PATTERN, HIGH_FLAIR_PATTERN

from ..actions.Retry import retry


@retry
def setFlair(state, winData, comment):
    rounds = winData["roundList"]
    numWins = len(rounds)

    oldFlair = comment.author_flair_text or ""
    flairText = ""
    customFlair = ""
    cssClass = "winner" if numWins == 1 else comment.author_flair_css_class

    if (numWins == 1 and not oldFlair == "") or \
            (1 < numWins <= 8 and not LOW_FLAIR_PATTERN(numWins - 1).match(oldFlair)) or \
            (numWins > 8 and not HIGH_FLAIR_PATTERN.match(oldFlair)):
        return # don't update flair if it doesn't match the given format

    if numWins < 8:
        flairText = "Round " + ", ".join([str(roundNum) for roundNum in rounds])
        if numWins > 1:
            customFlair = LOW_FLAIR_PATTERN(numWins - 1).sub("", oldFlair)
    else:
        flairText = "{} wins".format(numWins)
        if numWins == 8:
            customFlair = LOW_FLAIR_PATTERN(7).sub("", oldFlair)
        else:
            customFlair = HIGH_FLAIR_PATTERN.sub("", oldFlair)

    newFlair = flairText + customFlair

    state.subreddit.flair.set(winData["username"], text = newFlair, css_class = cssClass)

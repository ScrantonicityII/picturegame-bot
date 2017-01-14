def setFlair(submission, flair):
    flairs = submission.flair.choices()
    correctFlair = next(f for f in flairs if f["flair_text"] == flair)
    flairId = correctFlair["flair_template_id"]
    submission.flair.select(flairId)

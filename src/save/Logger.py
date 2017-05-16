from time import time, strftime

from .. import config

LEVELS = { 'e': 0, 'w': 1, 'i': 2, 'd': 3 }

groupIds = {}
currentId = 0

def log(text, level = 'i', groupId = None, discard = True):
    global currentId

    currentTime = time()

    if groupId is None:
        groupId = currentId
        groupIds[currentId] = currentTime
        currentId += 1

    timeDifference = currentTime - groupIds[groupId]
    timeString = strftime("[%Y-%m-%d %H:%M:%S]") + \
        ("[+{:.3f}]".format(timeDifference) if timeDifference > 0 else "")

    if discard:
        groupIds.pop(groupId, None)

    if config.getKey("logLevel") is not None and LEVELS[config.getKey("logLevel")] < LEVELS[level]:
        return

    logString = "{}[{}] {}".format(timeString, level, text)

    with open("data/bot.log", "a") as logFile:
        logFile.write(logString + "\n")

    if config.getKey("printLogs") in { "y", None }:
        print(logString)

    return groupId

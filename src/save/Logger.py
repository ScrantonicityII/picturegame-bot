from time import strftime

import config

def log(text, method = 'a'):
    with open("data/bot.log", method) as logFile:
        logFile.write(strftime("[%Y-%m-%d %H:%M:%S] ") + text + "\n")

    if config.getKey("printLogs") == "y":
        print(text)

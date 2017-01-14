from time import strftime

def log(text, method = 'a'):
    with open("data/bot.log", method) as logFile:
        logFile.write(strftime("[%Y-%m-%d %H:%M:%S] ") + text + "\n")

from time import sleep

from save import Logger

def actionWithRetry(action, *args):
    '''Perform the given action. If an exception is raised, retry every ten seconds
    Return the return value of the action, if any'''

    while True:
        try:
            result = action(*args)
            return result
        except Exception as e:
            Logger.log("Action {} failed with error message: {}, retrying in 10 seconds...".format(action.__name__, e))
            sleep(10)
            continue

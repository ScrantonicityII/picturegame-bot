from prawcore import exceptions
from time import sleep
import traceback

from save import Logger

def retry(action):
    def actionWithRetry(*args, **kwargs):
        '''Perform the given action. If an exception is raised, retry every ten seconds
        Return the return value of the action, if any'''

        failCount = 0
        groupId = 0
        while True:
            try:
                result = action(*args, **kwargs)

                if failCount > 0:
                    Logger.log("Action {} succeeded after {} failures".format(action.__name__, failCount), 'w', groupId)

                return result

            except exceptions.BadRequest:
                # Don't keep trying if we get a bad request - this is likely caused by deleted accounts so we can safely ignore them
                Logger.log("Action {} failed with HTTP status 400. Returning...".format(action.__name__), 'w')
                return

            except Exception as e:
                failCount += 1

                if failCount == 1:
                    groupId = Logger.log("Action {} failed with error message: {}".format(action.__name__, e), 'e', discard = False)
                    Logger.log("Stacktrace:\n{}".format("".join(traceback.format_stack())), 'e')

                sleep(10)
                continue

    return actionWithRetry

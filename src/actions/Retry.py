import logging
from time import sleep
import traceback

from prawcore import exceptions

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
                    logging.warn("Action %s succeeded after %d failures", action.__name__, failCount)

                return result

            except exceptions.BadRequest:
                # Don't keep trying if we get a bad request
                # This is likely caused by deleted accounts so we can safely ignore them
                logging.warn("Action %s failed with HTTP status 400. Returning...", action.__name__)
                return

            except Exception:
                failCount += 1

                if failCount == 1:
                    logging.error(traceback.format_exc())

                sleep(10)
                continue

    return actionWithRetry

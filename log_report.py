import logging
import datetime

def log_info(message):
    current_time = datetime.datetime.now().isoformat()
    log_message = "{}: {}".format(current_time, message)

    print(log_message)
    logging.info(log_message)
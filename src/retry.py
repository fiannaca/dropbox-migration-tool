import time
import random
import logging
from functools import wraps

def retry_on_exception(exception, max_retries=5, initial_delay=1, backoff_factor=2, should_retry=None):
    """
    A decorator to retry a function call on a specific exception.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    if i == max_retries - 1:
                        logging.error(f"Final attempt failed. Exception: {e}")
                        raise
                    
                    if should_retry and not should_retry(e):
                        raise e

                    logging.warning(f"Attempt {i + 1} failed with {e}. Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    delay *= backoff_factor
                    delay += random.uniform(0, 1) # Add jitter
        return wrapper
    return decorator

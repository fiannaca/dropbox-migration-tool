import logging
import sys

def setup_logger():
    """
    Configures the logger to write to a file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='migration.log',
        filemode='a'
    )

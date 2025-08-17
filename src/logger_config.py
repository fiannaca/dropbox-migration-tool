import logging
import sys

def setup_logger():
    """
    Configures the logger to write to a file and the console.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("migration.log")
        ]
    )

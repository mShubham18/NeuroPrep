import contextlib
import logging

class TryExcept(contextlib.ContextDecorator):
    """TryExcept context manager for error handling and logging."""
    
    def __init__(self, msg='', verbose=True):
        self.msg = msg
        self.verbose = verbose
    
    def __enter__(self):
        pass
    
    def __exit__(self, exc_type, value, traceback):
        if self.verbose and value is not None:
            print(f'{self.msg}{": " if self.msg else ""}{value}')
        return True  # suppress any exceptions

def init_logging(name=__name__, level=logging.INFO):
    """Initialize logger with specified name and level."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

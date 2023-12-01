import logging

# Initialize error_logger
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
handler = logging.FileHandler('errors.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
error_logger.addHandler(handler)


# Initialize console_logger
console_logger = logging.getLogger('console_logger')
console_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s - %(extra_var)s', defaults={'extra_var': ' '}))
console_logger.addHandler(handler)


def initialize_logger(name, level=logging.DEBUG):
    """Initialize a logger with the given name and level."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

def create_simple_formatter():
    """Create a simple formatter without timestamps."""
    return logging.Formatter('%(levelname)s - %(message)s')

def add_stream_handler(logger, level=logging.DEBUG, formatter=None):
    """Add a stream handler to the logger."""
    handler = logging.StreamHandler()
    handler.setLevel(level)
    if formatter is None:
        formatter = create_simple_formatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def add_file_handler(logger, filename, level=logging.ERROR, formatter=None):
    """Add a file handler to the logger."""
    handler = logging.FileHandler(filename)
    handler.setLevel(level)
    if formatter is None:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def setup_logger(name, level=logging.DEBUG):
    """Setup a logger with the given name and level."""
    logger = initialize_logger(name, level)
    add_stream_handler(logger, level)
    return logger

def setup_error_logger(name, filename):
    """Setup an error logger with the given name and filename."""
    logger = initialize_logger(name, logging.ERROR)
    add_file_handler(logger, filename)
    return logger
import datetime
import logging
import os
import sys
from colorlog import ColoredFormatter
from contextlib import contextmanager
from typing import Generator, List, Optional

# directory for instance logs if running from project root:
LOG_DIR = os.path.join(os.getcwd(), "attackmate_server_logs")
# Or absolute path:
# LOG_DIR = "/var/log/attackmate_instances" # must exists and has write permissions

# List of logger names to add instance-specific handlers to
TARGET_LOGGER_NAMES = ['playbook', 'output', 'json']
API_CONSOLE_FORMAT = '  %(asctime)s %(log_color)s%(levelname)-8s%(reset)s | API | %(log_color)s%(message)s%(reset)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

api_logger = logging.getLogger('attackmate_api')

# Create  formatter for the instance files
instance_log_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
json_log_formatter = logging.Formatter('%(message)s')

def initialize_api_logger(debug: bool, append_logs: bool) -> logging.Logger:
    api_logger = logging.getLogger('attackmate_api')
    api_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Console handler for API logs
    if not has_stdout_handler(api_logger):
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = ColoredFormatter(API_CONSOLE_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter)
        api_logger.addHandler(console_handler)

    #  File handler for API logs ?
    # api_file_formatter = logging.Formatter(API_CONSOLE_FORMAT, datefmt=DATE_FORMAT)
    # api_file_handler = create_file_handler('attackmate_api.log', append_logs, api_file_formatter)
    # api_logger.addHandler(api_file_handler)

    # Prevent propagation to avoid duplicate logs if root logger also has handlers
    api_logger.propagate = False

    return api_logger

def has_stdout_handler(logger: logging.Logger) -> bool:
    """
    Checks if a logger already has a StreamHandler directed to stdout.

    """
    return any(
        isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout
        for handler in logger.handlers
    )

@contextmanager
def instance_logging(instance_id: str, log_level: int = logging.INFO) -> Generator[List[Optional[str]], None, None]:
    """
    Context manager to temporarily add a file handler for a specific instance
    to the target AttackMate loggers.
    """
    handlers: List[logging.FileHandler] = []
    instance_output_log_file = None  
    instance_attackmate_log_file = None

    try:
        # log directory exists
        os.makedirs(LOG_DIR, exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        instance_output_log_file = os.path.join(LOG_DIR, f"{timestamp}_{instance_id}_output.log")
        instance_attackmate_log_file = os.path.join(LOG_DIR, f"{timestamp}_{instance_id}_attackmate.log")
        instance_json_log_file = os.path.join(LOG_DIR, f"{timestamp}_{instance_id}_attackmate.json")

        # instance-specific file handler
        #  'a' to append within the same request if multiple logs occur
        # each request gets a new timestamped file.
        output_file_handler = logging.FileHandler(instance_output_log_file, mode='a')
        output_file_handler.setFormatter(instance_log_formatter)
        output_file_handler.setLevel(log_level)

        attackmate_file_handler = logging.FileHandler(instance_attackmate_log_file, mode='a')
        attackmate_file_handler.setFormatter(instance_log_formatter)
        attackmate_file_handler.setLevel(log_level)

        attackmate_json_handler = logging.FileHandler(instance_json_log_file, mode='a')
        attackmate_json_handler.setFormatter(json_log_formatter)
        attackmate_json_handler.setLevel(log_level)

        # Add the handler to the target loggers
        for logger_name in TARGET_LOGGER_NAMES:
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)
            logger.propagate = False
            if logger_name == 'playbook':
                logger.addHandler(attackmate_file_handler)
                handlers.append(attackmate_file_handler)  # remove later finally
            if logger_name == 'output':
                logger.addHandler(output_file_handler)
                handlers.append(output_file_handler)  # remove later in finally
            if logger_name == 'json':
                logger.addHandler(attackmate_json_handler)
                handlers.append(attackmate_json_handler)  # remove later in finally
            api_logger.info(
                (f"Added instance log handlers for '{instance_id}' to logger '{logger_name}' -> "
                 f"{instance_output_log_file} and {instance_attackmate_log_file} and {instance_json_log_file}."))
        yield [
            instance_attackmate_log_file,
            instance_output_log_file,
            instance_json_log_file
        ]  # 'with' block executes here and uses these paths

    except Exception as e:
        api_logger.error(f"Error setting up instance logging for '{instance_id}': {e}", exc_info=True)
        yield  # main code execution if logging fails

    finally:
        logger.info(f"Removing instance log handlers for '{instance_id}'...")
        for handler in handlers:
            for logger_name in TARGET_LOGGER_NAMES:
                logger = logging.getLogger(logger_name)
                if handler in logger.handlers:
                    logger.removeHandler(handler)
            try:
                handler.close()
            except Exception as e:
                api_logger.error(
                    f"Error removing/closing log handler for instance '{instance_id}': {e}", exc_info=True)
        api_logger.info(f"Instance log handlers removed for '{instance_id}'.")

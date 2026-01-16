from typing import Optional
import logging

class ConsoleLogger:
    """Custom logging class.
    """
    def __init__(
        self,
        name: str = "default_logger",
        level:str = "DEBUG",
        filename: Optional[str] = None,
    ) -> None:

        accepted_values = [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]

        if level not in accepted_values:
          raise ValueError(
              "The value given to the variable is not an accepted value."
          )

        logging_level = {
          "DEBUG": logging.DEBUG,
          "INFO": logging.INFO,
          "WARNING": logging.WARNING,
          "ERROR": logging.ERROR,
          "CRITICAL": logging.CRITICAL,
        }

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging_level[level])

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging_level[level])

        formatter = logging.Formatter(
          '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        if filename:
            file_handler = logging.FileHandler(filename=filename)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

base_logger = ConsoleLogger()

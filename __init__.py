import os
import json
import datetime

__version__ = '0.1.0'


class LoggerInterface:
    """
    PHP PSR-3 Logger interface port.
    See https://www.php-fig.org/psr/psr-3/
    """
    def emergency(self, message: str, context: dict = None):
        """ System is unusable. """

        raise NotImplementedError

    def alert(self, message: str, context: dict = None):
        """
        Action must be taken immediately.

        Example: Entire website down, database unavailable, etc. This should trigger the SMS alerts and wake you up.
        """
        raise NotImplementedError

    def critical(self, message: str, context: dict = None):
        """
        Critical conditions.

        Example: Application component unavailable, unexpected exception.
        """
        raise NotImplementedError

    def error(self, message: str, context: dict = None):
        """ Runtime errors that do not require immediate action but should typically be logged and monitored. """
        raise NotImplementedError

    def warning(self, message: str, context: dict = None):
        """
        Exceptional occurrences that are not errors.

        Example: Use of deprecated APIs, poor use of an API, undesirable things that are not necessarily wrong.
        """
        raise NotImplementedError

    def notice(self, message: str, context: dict = None):
        """ Normal but significant events. """
        raise NotImplementedError

    def info(self, message: str, context: dict = None):
        """
        Interesting events.

        Example: User logs in, SQL logs.
        """
        raise NotImplementedError

    def debug(self, message: str, context: dict = None):
        """ Detailed debug information. """
        raise NotImplementedError

    def log(self, level: str, message: str, context: dict = None):
        """ Logs with an arbitrary level. """
        raise NotImplementedError


class SimpleLogger(LoggerInterface):
    """
    Simple PSR-3 (PHP Standard) logger implementation for Python.

    Example 1:

        # Main instance initialization with absolute path to log file
        logger = SimpleLogger(filename='/var/log/my-app.log')

        # Log some message
        logger.info('Client registration process started', context={'client_data': dict(client_data)})

    Logger may be forked to log messages to other channel of same file.

    Example 2:

        # ... code from example 1 goes here ...

        # Factory method to create logger proxy instance that bind to same file but writes log messages in other channel
        notification_subsystem_logger = logger.fork('notification_subsystem')

        # Log some message
        notification_subsystem_logger.critical('Unable to send notification to user', {'user_id': user.id })

    """

    EMERGENCY = 'EMERGENCY'
    ALERT = 'ALERT'
    CRITICAL = 'CRITICAL'
    ERROR = 'ERROR'
    WARNING = 'WARNING'
    NOTICE = 'INFO'
    INFO = 'INFO'
    DEBUG = 'DEBUG'

    _DEFAULT_CHANNEL = 'app'

    def __init__(self, filename: str):
        if os.path.exists(filename):
            mode = 'a'  # append if already exists
        else:
            mode = 'w'  # make a new file if not exists
        self.fp = open(filename, mode)

        self._proxy_registry = {}
        self.fork(channel=self._DEFAULT_CHANNEL)

    def __del__(self):
        if not self.fp.closed:
            self.fp.close()

        for logger_channel_proxy in self._proxy_registry:
            del self._proxy_registry[logger_channel_proxy]

    # todo decide to do not use because too many overloads in child class
    # def __call__(self, channel: str) -> 'SimpleLoggerProxy':
    #     return self.fork(channel=channel)

    def fork(self, channel: str) -> 'SimpleLoggerProxy':
        # fixme naming things: use, fork, switch
        """ Creates and returns logger fork for a channel or simply returns it if already exists with this name. """
        if channel in self._proxy_registry:
            return self._proxy_registry[channel]

        self._proxy_registry[channel] = SimpleLoggerProxy(
            logger=self,
            channel=channel,
        )

        return self._proxy_registry[channel]

    def write(self, channel: str, level: str, message: str, context: dict = None, extra: dict = None):
        """ Writes a log message """
        if context is None:
            context = []

        if extra is None:
            extra = []

        log_entry = '[{date!s}] {channel!s}.{level!s}: {message!s} {context!s} {extra!s}\n'.format(
            date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            channel=channel.lower(),
            level=level.upper(),
            message=message,
            context=json.dumps(context),
            extra=extra,
        )

        self.fp.write(log_entry)
        self.fp.flush()

    def emergency(self, message: str, context: dict = None):
        self.log(level=self.EMERGENCY, message=message, context=context)

    def alert(self, message: str, context: dict = None):
        self.log(level=self.ALERT, message=message, context=context)

    def critical(self, message: str, context: dict = None):
        self.log(level=self.CRITICAL, message=message, context=context)

    def error(self, message: str, context: dict = None):
        self.log(level=self.ERROR, message=message, context=context)

    def warning(self, message: str, context: dict = None):
        self.log(level=self.WARNING, message=message, context=context)

    def notice(self, message: str, context: dict = None):
        self.log(level=self.NOTICE, message=message, context=context)

    def info(self, message: str, context: dict = None):
        self.log(level=self.INFO, message=message, context=context)

    def debug(self, message: str, context: dict = None):
        self.log(level=self.DEBUG, message=message, context=context)

    def log(self, level: str, message: str, context: dict = None):
        self.fork(channel=self._DEFAULT_CHANNEL).log(level=level, message=message, context=context)


class SimpleLoggerProxy(SimpleLogger):
    # noinspection PyMissingConstructor
    def __init__(self, logger: SimpleLogger, channel: str):
        self.logger = logger
        self.channel = channel

        # do not call parent constructor

    def __del__(self):
        pass  # do nothing. override parent behaviour

    def fork(self, channel: str) -> 'SimpleLoggerProxy':
        return self.logger.fork(channel=channel)  # proxy call to parent

    def log(self, level: str, message: str, context: dict = None):
        self.logger.write(channel=self.channel, level=level, message=message, context=context)  # proxy call to parent

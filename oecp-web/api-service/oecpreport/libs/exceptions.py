#!/usr/bin/python3


class Error(Exception):

    """
    Description: Read the configuration file base class in the system
    Attributes:
        message:Exception information
    """

    def __init__(self, msg=""):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


class ContentNoneException(Error):
    """
    Description: Content is empty exception
    Attributes:
    """

    def __init__(self, message):
        Error.__init__(self, "No content: %r" % (message,))


class DbnameNoneException(ContentNoneException):
    """
    Description: Exception with empty database name
    Attributes:
    """

    def __init__(self, message):
        ContentNoneException.__init__(self, "%r" % (message,))


class DatabaseException(Error):
    """
    Description: Content is empty exception
    Attributes:
    """

    def __init__(self, message):
        Error.__init__(self, "No content: %r" % (message,))

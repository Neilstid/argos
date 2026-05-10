class SourceValidationError(ValueError):
    """
    Raised when a source (URL, channel) is invalid.
    
    This exception is raised when attempting to add or validate a data source
    (such as a YouTube channel, RSS feed URL, or other source) that is
    invalid or cannot be accessed.
    
    Attributes:
        message (str): Description of the validation error
    
    Example:
        >>> raise SourceValidationError("Invalid RSS feed URL: not a valid URL")
        SourceValidationError: Invalid RSS feed URL: not a valid URL
    """
    pass

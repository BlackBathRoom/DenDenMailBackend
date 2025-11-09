class ModelNotLoadedError(Exception):
    """Raised when the AI model is not loaded in application resources."""


class ModelBusyError(Exception):
    """Raised when the AI model is currently busy processing another request."""

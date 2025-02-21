class WorkerException(Exception):
    """Base class for exceptions in the worker module."""
    pass
  
  
class MissingContext(WorkerException):
    """Exception raised for missing context in the worker module."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class OutOfSubject(WorkerException):
    """Exception raised for out of subject in the worker module."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
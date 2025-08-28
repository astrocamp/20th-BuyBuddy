class GroupServiceException(Exception):
    pass

class GroupNotFoundException(GroupServiceException):
    pass

class GroupClosedException(GroupServiceException):
    pass

class AlreadyJoinedException(GroupServiceException):
    pass

class ExceedsLimitException(GroupServiceException):
    pass

class InsufficientQuantityException(GroupServiceException):
    pass

class ProductNotFoundException(GroupServiceException):
    pass

class JoinedGroupException(GroupServiceException):
    pass
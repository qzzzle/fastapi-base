"""
Small convenience wrappers for HTTP errors.
- Keep the same public API you already use (status codes and messages).
"""

from fastapi import HTTPException, status


class DuplicatedError(HTTPException):
    def __init__(self, detail: str = "Duplicated"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class AuthError(HTTPException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Not Found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ValidationError(HTTPException):
    def __init__(self, detail: str = "Validation Error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

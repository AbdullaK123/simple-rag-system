from typing import Union, Awaitable, Callable
import asyncio
from typing import ParamSpec, TypeVar
from fastapi import HTTPException, status
from functools import wraps
from app.config.logging import logger

P = ParamSpec('P')
R = TypeVar('R')

def handle_unchecked_errors(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            result = await func(*args, **kwargs)
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unchecked exception in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred"
            ) from e
    
    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            result = func(*args, **kwargs)
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unchecked exception in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred"
            ) from e
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
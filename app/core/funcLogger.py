import logging
import functools
import json
import time
from typing import Callable, Any
import traceback
import inspect
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JsonEncoder(json.JSONEncoder):
    """Enhanced JSON encoder to handle various Python objects"""
    def default(self, obj):
        try:
            if hasattr(obj, "dict") and callable(obj.dict):
                return obj.dict()
            elif hasattr(obj, "__dict__"):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            elif hasattr(obj, "__str__"):
                return str(obj)
            return super().default(obj)
        except:
            return str(obj)

def log_function(func: Callable):
    """Decorator to log function inputs, outputs, and execution time"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        function_name = func.__qualname__
        start_time = time.time()
        
        # Log input parameters with ensure_ascii=False
        params = {
            "args": [json.dumps(arg, cls=JsonEncoder, ensure_ascii=False) for arg in args],
            "kwargs": {k: json.dumps(v, cls=JsonEncoder, ensure_ascii=False) for k, v in kwargs.items()}
        }
        logger.info(f"Calling {function_name} with params: {json.dumps(params, cls=JsonEncoder, ensure_ascii=False)}")
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Log result and execution time
            execution_time = time.time() - start_time
            logger.info(
                f"{function_name} completed in {execution_time:.2f}s with result: "
                f"{json.dumps(result, cls=JsonEncoder, ensure_ascii=False)}"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{function_name} failed after {execution_time:.2f}s with error: {str(e)}\n"
                f"{traceback.format_exc()}"
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        function_name = func.__qualname__
        start_time = time.time()
        
        # Log input parameters with ensure_ascii=False
        params = {
            "args": [json.dumps(arg, cls=JsonEncoder, ensure_ascii=False) for arg in args],
            "kwargs": {k: json.dumps(v, cls=JsonEncoder, ensure_ascii=False) for k, v in kwargs.items()}
        }
        logger.info(f"Calling {function_name} with params: {json.dumps(params, cls=JsonEncoder, ensure_ascii=False)}")
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Log result and execution time
            execution_time = time.time() - start_time
            logger.info(
                f"{function_name} completed in {execution_time:.2f}s with result: "
                f"{json.dumps(result, cls=JsonEncoder, ensure_ascii=False)}"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{function_name} failed after {execution_time:.2f}s with error: {str(e)}\n"
                f"{traceback.format_exc()}"
            )
            raise

    # Choose the appropriate wrapper based on whether the function is async or not
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
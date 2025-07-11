import logging
import functools
import json
import time
from typing import Callable, Any
import traceback
import inspect
import asyncio
from datetime import datetime
import socket
import os

# Configure custom log formatter with timestamp and process info
log_format = '%(asctime)s [%(levelname)s] [PID:%(process)d] [%(name)s] - %(message)s'
formatter = logging.Formatter(log_format)

# Get file handler
log_file = 'application.log'
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)

# Get console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler], force=True)
logger = logging.getLogger(__name__)

# Get hostname for logging
hostname = socket.gethostname()

class JsonEncoder(json.JSONEncoder):
    """Enhanced JSON encoder to handle various Python objects"""
    def default(self, obj):
        try:
            if hasattr(obj, "model_dump") and callable(obj.model_dump):  # For Pydantic v2
                return obj.model_dump()
            elif hasattr(obj, "dict") and callable(obj.dict):  # For Pydantic v1
                return obj.dict()
            elif isinstance(obj, datetime):
                return obj.isoformat()
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
        request_id = f"{int(time.time() * 1000)}-{os.getpid()}"
        
        # Extract client IP if request object is available
        client_ip = "N/A"
        for arg in args:
            if hasattr(arg, "client") and hasattr(arg.client, "host"):
                client_ip = arg.client.host
                break
        
        # Basic context info
        context_info = {
            "timestamp": datetime.now().isoformat(),
            "hostname": hostname,
            "request_id": request_id,
            "client_ip": client_ip,
            "function": function_name
        }
        
        # Log input parameters
        params = {
            "args": [json.dumps(arg, cls=JsonEncoder, ensure_ascii=False) for arg in args],
            "kwargs": {k: json.dumps(v, cls=JsonEncoder, ensure_ascii=False) for k, v in kwargs.items()}
        }
        
        log_entry = {
            "context": context_info,
            "request": params
        }
        
        logger.info(f"Request {request_id} from {client_ip}: {json.dumps(log_entry, ensure_ascii=False)}")
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            response_log = {
                "context": context_info,
                "response": json.dumps(result, cls=JsonEncoder, ensure_ascii=False),
                "execution_time_ms": int(execution_time * 1000)
            }
            
            logger.info(f"Response {request_id} to {client_ip} ({execution_time:.2f}s): {json.dumps(response_log, ensure_ascii=False)}")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error_log = {
                "context": context_info,
                "error": str(e),
                "execution_time_ms": int(execution_time * 1000),
                "traceback": traceback.format_exc()
            }
            logger.error(f"Error {request_id} for {client_ip} ({execution_time:.2f}s): {json.dumps(error_log, ensure_ascii=False)}")
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        function_name = func.__qualname__
        start_time = time.time()
        request_id = f"{int(time.time() * 1000)}-{os.getpid()}"
        
        # Extract client IP if request object is available
        client_ip = "N/A"
        for arg in args:
            if hasattr(arg, "client") and hasattr(arg.client, "host"):
                client_ip = arg.client.host
                break
        
        # Basic context info
        context_info = {
            "timestamp": datetime.now().isoformat(),
            "hostname": hostname,
            "request_id": request_id,
            "client_ip": client_ip,
            "function": function_name
        }
        
        # Log input parameters
        params = {
            "args": [json.dumps(arg, cls=JsonEncoder, ensure_ascii=False) for arg in args],
            "kwargs": {k: json.dumps(v, cls=JsonEncoder, ensure_ascii=False) for k, v in kwargs.items()}
        }
        
        log_entry = {
            "context": context_info,
            "request": params
        }
        
        logger.info(f"Request {request_id} from {client_ip}: {json.dumps(log_entry, ensure_ascii=False)}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            response_log = {
                "context": context_info,
                "response": json.dumps(result, cls=JsonEncoder, ensure_ascii=False),
                "execution_time_ms": int(execution_time * 1000)
            }
            
            logger.info(f"Response {request_id} to {client_ip} ({execution_time:.2f}s): {json.dumps(response_log, ensure_ascii=False)}")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error_log = {
                "context": context_info,
                "error": str(e),
                "execution_time_ms": int(execution_time * 1000),
                "traceback": traceback.format_exc()
            }
            logger.error(f"Error {request_id} for {client_ip} ({execution_time:.2f}s): {json.dumps(error_log, ensure_ascii=False)}")
            raise

    # Choose the appropriate wrapper based on whether the function is async or not
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
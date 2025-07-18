from pydantic import BaseModel
from typing import Any, Optional

class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Optional[Any] = None 

    @classmethod
    def success(cls, data: Optional[Any] = None):
        return cls(code=200, msg='请求成功', data=data)

    @classmethod
    def fail(cls, msg: str): 
        return cls(code=500, msg=msg, data=None)
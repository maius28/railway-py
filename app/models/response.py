from pydantic import BaseModel
from typing import Any, Optional

class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Optional[Any] = None 

    def success(self, data: Optional[Any]):
        self.code = 200
        self.msg = '请求成功'
        self.data = data

    def fail(self, msg : str): 
        self.code = 500
        self.msg = msg
        self.data = None
from pydantic import BaseModel
from typing import List, Optional

class ReferralNode(BaseModel):
    id: str
    email: str
    username: Optional[str]
    children: List["ReferralNode"] = []

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

from pydantic import BaseModel
from typing import Optional

class WbsBase(BaseModel):
    wbs: str
    wbs_type: Optional[str]
    project_name: Optional[str]
    budget_mm: Optional[float]
    budget_tot: Optional[float]
    salvata: bool = True

class WbsCreate(WbsBase):
    pass

class WbsUpdate(WbsBase):
    pass

class WbsResponse(WbsBase):
    class Config:
        orm_mode = True
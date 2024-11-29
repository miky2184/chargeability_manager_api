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

class ResourceBase(BaseModel):
    eid: str
    last_name: str
    first_name: str
    level: Optional[str]
    loaded_cost: Optional[float]
    office: Optional[str]
    dte: Optional[str]
    salvata: bool = True

class ResourceCreate(ResourceBase):
    pass

class ResourceUpdate(ResourceBase):
    pass

class ResourceResponse(ResourceBase):
    class Config:
        orm_mode = True

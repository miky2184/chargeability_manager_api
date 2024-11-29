from pydantic import BaseModel
from typing import Optional
from core.auth_config import verify_password

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
    level: float = None
    loaded_cost: float = None
    office: str = None
    dte: str = None
    salvata: bool = True

class ResourceCreate(ResourceBase):
    pass

class ResourceUpdate(ResourceBase):
    pass

class ResourceResponse(ResourceBase):
    class Config:
        orm_mode = True


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

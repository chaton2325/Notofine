from pydantic import BaseModel
from models.models import DeviceType
from datetime import datetime

# =================================
# Device Token Schemas
# =================================

class DeviceTokenBase(BaseModel):
    device_token: str
    device_type: DeviceType

class DeviceTokenCreate(DeviceTokenBase):
    user_email: str

class DeviceToken(DeviceTokenBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from models.models import SubscriptionStatus

# =================================
# Plan Schemas
# =================================

class PlanBase(BaseModel):
    name: str
    price: float
    duration_days: int
    description: Optional[str] = None
    is_active: bool = True

class PlanCreate(PlanBase):
    pass

class Plan(PlanBase):
    id: int

    class Config:
        orm_mode = True

class PlanUpdate(BaseModel):
    price: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# =================================
# Subscription Schemas
# =================================

class SubscriptionCreate(BaseModel):
    user_email: str
    plan_id: int
    auto_renew: bool = False

class Subscription(BaseModel):
    id: int
    user_id: int
    payment_status: SubscriptionStatus
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    plan: Plan # Affiche les détails du plan imbriqué

    class Config:
        orm_mode = True

class SubscriptionStatusResponse(BaseModel):
    is_subscribed: bool
    is_active: bool
    end_date: Optional[datetime] = None
    plan_name: Optional[str] = None
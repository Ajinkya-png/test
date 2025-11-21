"""
API Schemas
===========

This module defines Pydantic models used by FastAPI endpoints.
They map directly to ORM models defined in `database.py` and ensure
type-safe, validated data exchange between backend services and API clients.

Author: Ajinkya Goundadkar
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


# ============================================================
# ENUMS (match database enums)
# ============================================================
class OrderStatus(str, Enum):
    cart = "cart"
    placed = "placed"
    confirmed = "confirmed"
    preparing = "preparing"
    ready = "ready"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"
    completed = "completed"
    cancelled = "cancelled"


# ============================================================
# BASE CONFIG
# ============================================================
class ConfiguredModel(BaseModel):
    """Common config for all API schemas."""
    class Config:
        orm_mode = True
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================
# CUSTOMER SCHEMAS
# ============================================================
class CustomerCreate(ConfiguredModel):
    name: str
    phone_number: str = Field(..., regex=r"^\+?\d{10,15}$")
    email: Optional[EmailStr] = None
    address: Optional[dict] = None
    preferences: Optional[dict] = None
    payment_methods: Optional[dict] = None


class CustomerResponse(ConfiguredModel):
    id: int
    name: str
    phone_number: str
    email: Optional[str] = None
    address: Optional[dict] = None
    preferences: Optional[dict] = None
    payment_methods: Optional[dict] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


# ============================================================
# RESTAURANT SCHEMAS
# ============================================================
class RestaurantCreate(ConfiguredModel):
    name: str
    address: dict
    phone_number: Optional[str] = None
    operating_hours: Optional[dict] = None
    avg_prep_time: Optional[int] = 15
    rating: Optional[float] = 4.0


class RestaurantResponse(ConfiguredModel):
    id: int
    name: str
    phone_number: Optional[str]
    address: dict
    operating_hours: Optional[dict]
    avg_prep_time: int
    rating: float
    active: bool
    created_at: datetime
    updated_at: Optional[datetime]


# ============================================================
# MENU ITEM SCHEMAS
# ============================================================
class MenuItemCreate(ConfiguredModel):
    restaurant_id: int
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    is_available: bool = True
    customizations: Optional[dict] = None


class MenuItemResponse(ConfiguredModel):
    id: int
    restaurant_id: int
    name: str
    description: Optional[str]
    price: float
    category: Optional[str]
    is_available: bool
    customizations: Optional[dict]
    created_at: Optional[datetime] = None


# ============================================================
# DRIVER SCHEMAS
# ============================================================
class DriverCreate(ConfiguredModel):
    name: str
    phone_number: str
    vehicle_number: str
    current_location: Optional[dict] = None


class DriverResponse(ConfiguredModel):
    id: int
    name: str
    phone_number: str
    vehicle_number: str
    current_location: Optional[dict]
    is_available: bool
    rating: float
    created_at: datetime
    updated_at: Optional[datetime]


# ============================================================
# ORDER ITEM SCHEMAS
# ============================================================
class OrderItemBase(ConfiguredModel):
    menu_item_id: int
    quantity: int = 1
    price_each: float
    total_price: float
    customizations: Optional[dict] = None


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    menu_item: Optional[MenuItemResponse] = None


# ============================================================
# ORDER SCHEMAS
# ============================================================
class OrderCreate(ConfiguredModel):
    customer_id: int
    restaurant_id: int
    items: List[OrderItemBase]
    delivery_address: dict
    payment_info: Optional[dict] = None


class OrderResponse(ConfiguredModel):
    id: int
    customer_id: int
    restaurant_id: int
    driver_id: Optional[int] = None
    status: OrderStatus
    total_amount: float
    delivery_address: dict
    payment_info: Optional[dict]
    timeline: Optional[dict]
    created_at: datetime
    updated_at: Optional[datetime]
    is_deleted: bool = False
    items: Optional[List[OrderItemResponse]] = None


# ============================================================
# CALL SESSION SCHEMAS
# ============================================================
class CallSessionCreate(ConfiguredModel):
    call_sid: str
    customer_id: Optional[int] = None
    transcript: Optional[str] = None
    metrics: Optional[dict] = None
    outcome: Optional[str] = None


class CallSessionResponse(ConfiguredModel):
    id: int
    call_sid: str
    customer_id: Optional[int]
    transcript: Optional[str]
    metrics: Optional[dict]
    outcome: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    is_completed: bool


# ============================================================
# AGENT TRANSITION SCHEMAS
# ============================================================
class AgentTransitionCreate(ConfiguredModel):
    call_session_id: int
    from_agent: str
    to_agent: str
    summary: str


class AgentTransitionResponse(ConfiguredModel):
    id: int
    call_session_id: int
    from_agent: str
    to_agent: str
    summary: str
    timestamp: datetime


# ============================================================
# COMBINED / NESTED RESPONSE MODELS
# ============================================================

class CustomerWithOrders(CustomerResponse):
    """Customer details with order history."""
    orders: Optional[List[OrderResponse]] = None


class RestaurantWithMenu(RestaurantResponse):
    """Restaurant details with menu items."""
    menu: Optional[List[MenuItemResponse]] = None


class OrderDetailedResponse(OrderResponse):
    """Order details with linked customer, restaurant, driver."""
    customer: Optional[CustomerResponse] = None
    restaurant: Optional[RestaurantResponse] = None
    driver: Optional[DriverResponse] = None

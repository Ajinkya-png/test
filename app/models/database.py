from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, DateTime, Boolean,
    JSON, Enum, func, UniqueConstraint, Index, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column
import enum
import datetime

Base = declarative_base()


# -------------------------
# ENUMS
# -------------------------
class OrderStatus(str, enum.Enum):
    CART = "cart"
    PLACED = "placed"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# -------------------------
# MODELS
# -------------------------
class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=True)
    address: Mapped[dict] = mapped_column(JSONB, nullable=True)
    preferences: Mapped[dict] = mapped_column(JSONB, nullable=True)
    payment_methods: Mapped[dict] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    orders = relationship("Order", back_populates="customer")

    def __repr__(self):
        return f"<Customer(name={self.name}, phone={self.phone_number})>"


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[dict] = mapped_column(JSONB)
    operating_hours: Mapped[dict] = mapped_column(JSONB)
    menu = relationship("MenuItem", back_populates="restaurant")

    avg_prep_time: Mapped[int] = mapped_column(Integer, default=15)
    rating: Mapped[float] = mapped_column(Float, default=4.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now())


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(50))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    customizations: Mapped[dict] = mapped_column(JSONB, nullable=True)

    restaurant = relationship("Restaurant", back_populates="menu")
    order_items = relationship("OrderItem", back_populates="menu_item")

    __table_args__ = (
        Index("ix_menuitem_name", "name"),
    )


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone_number: Mapped[str] = mapped_column(String(20), unique=True)
    vehicle_number: Mapped[str] = mapped_column(String(50))
    current_location: Mapped[dict] = mapped_column(JSONB, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    rating: Mapped[float] = mapped_column(Float, default=4.5)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=True)

    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.CART)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_address: Mapped[dict] = mapped_column(JSONB)
    payment_info: Mapped[dict] = mapped_column(JSONB, nullable=True)
    timeline: Mapped[dict] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now())

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    customer = relationship("Customer", back_populates="orders")
    restaurant = relationship("Restaurant")
    driver = relationship("Driver")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    customizations: Mapped[dict] = mapped_column(JSONB, nullable=True)
    price_each: Mapped[float] = mapped_column(Float)
    total_price: Mapped[float] = mapped_column(Float)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")


class CallSession(Base):
    __tablename__ = "call_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_sid: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=True)
    outcome: Mapped[str] = mapped_column(String(120), nullable=True)

    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    ended_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    agent_transitions = relationship("AgentTransition", back_populates="call_session")


class AgentTransition(Base):
    __tablename__ = "agent_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_session_id: Mapped[int] = mapped_column(ForeignKey("call_sessions.id"))
    from_agent: Mapped[str] = mapped_column(String(50))
    to_agent: Mapped[str] = mapped_column(String(50))
    summary: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())

    call_session = relationship("CallSession", back_populates="agent_transitions")

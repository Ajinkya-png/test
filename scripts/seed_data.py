"""
Database seed script for Food Delivery Voice AI
-------------------------------------------------
Populates the PostgreSQL database with sample data:
- Customers
- Restaurants
- Menu Items
- Drivers
- (Optional) Demo orders

Run:
    python scripts/seed_data.py
"""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.database import Customer, Restaurant, MenuItem, Driver, Order, OrderItem, Base


def seed_customers(session: Session):
    customers = [
        Customer(
            name="Ajinkya Goundadkar",
            phone_number="+911234567890",
            email="ajinkya@example.com",
            address={"street": "KLE University Road", "city": "Belgaum", "zip": "590010"},
            preferences={"diet": "vegetarian"},
            payment_methods={"default": "card_1234"},
        ),
        Customer(
            name="Riya Sharma",
            phone_number="+919876543210",
            email="riya@example.com",
            address={"street": "MG Road", "city": "Pune", "zip": "411001"},
            preferences={"diet": "non-veg"},
        ),
    ]
    session.add_all(customers)
    session.commit()
    print(f"✅ Seeded {len(customers)} customers.")


def seed_restaurants(session: Session):
    restaurants = [
        Restaurant(
            name="Veggie Delight",
            phone_number="+912223334445",
            address={"street": "College Road", "city": "Belgaum"},
            operating_hours={"open": "09:00", "close": "22:00"},
            avg_prep_time=20,
        ),
        Restaurant(
            name="Spice Hub",
            phone_number="+912345678900",
            address={"street": "Jayanagar", "city": "Bangalore"},
            operating_hours={"open": "10:00", "close": "23:00"},
            avg_prep_time=25,
        ),
    ]
    session.add_all(restaurants)
    session.commit()
    print(f"✅ Seeded {len(restaurants)} restaurants.")
    return restaurants


def seed_menu_items(session: Session, restaurants):
    items = [
        MenuItem(
            restaurant_id=restaurants[0].id,
            name="Paneer Butter Masala",
            description="Creamy tomato gravy with cottage cheese.",
            price=220.0,
            category="Main Course",
            customizations={"spice": ["mild", "medium", "hot"]},
        ),
        MenuItem(
            restaurant_id=restaurants[0].id,
            name="Veg Biryani",
            description="Aromatic rice with vegetables and spices.",
            price=180.0,
            category="Rice",
        ),
        MenuItem(
            restaurant_id=restaurants[1].id,
            name="Chicken Curry",
            description="Traditional spicy chicken curry.",
            price=250.0,
            category="Main Course",
        ),
        MenuItem(
            restaurant_id=restaurants[1].id,
            name="Tandoori Roti",
            description="Whole wheat roti baked in clay oven.",
            price=30.0,
            category="Breads",
        ),
    ]
    session.add_all(items)
    session.commit()
    print(f"✅ Seeded {len(items)} menu items.")


def seed_drivers(session: Session):
    drivers = [
        Driver(
            name="Rahul Deshmukh",
            phone_number="+919111112222",
            vehicle_number="KA09DR1234",
            current_location={"lat": 15.860, "lon": 74.505},
            is_available=True,
        ),
        Driver(
            name="Sneha Patil",
            phone_number="+919333344445",
            vehicle_number="MH12SP4567",
            current_location={"lat": 15.875, "lon": 74.490},
            is_available=True,
        ),
    ]
    session.add_all(drivers)
    session.commit()
    print(f"✅ Seeded {len(drivers)} drivers.")


def seed_demo_orders(session: Session):
    """Optional demo orders to show system behavior."""
    customer = session.query(Customer).first()
    restaurant = session.query(Restaurant).first()
    driver = session.query(Driver).first()
    menu_item = session.query(MenuItem).first()

    if not all([customer, restaurant, driver, menu_item]):
        print("⚠️ Missing dependencies for demo order. Skipping.")
        return

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        driver_id=driver.id,
        status="preparing",
        total_amount=menu_item.price,
        delivery_address=customer.address,
        payment_info={"method": "card", "status": "paid"},
    )
    session.add(order)
    session.commit()

    order_item = OrderItem(
        order_id=order.id,
        menu_item_id=menu_item.id,
        quantity=1,
        customizations={"spice": "medium"},
        price_each=menu_item.price,
        total_price=menu_item.price,
    )
    session.add(order_item)
    session.commit()

    print(f"✅ Created demo order #{order.id} for customer {customer.name}.")


def main():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    seed_customers(session)
    restaurants = session.query(Restaurant).all()
    if not restaurants:
        seed_restaurants(session)
        restaurants = session.query(Restaurant).all()

    seed_menu_items(session, restaurants)
    seed_drivers(session)
    seed_demo_orders(session)

    session.close()
    print("🎉 Database seeding completed successfully.")


if __name__ == "__main__":
    main()

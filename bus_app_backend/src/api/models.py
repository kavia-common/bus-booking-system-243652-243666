"""SQLAlchemy models for Bus Booking MVP."""
from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from src.api.db import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String, nullable=False, index=True)
    destination = Column(String, nullable=False, index=True)
    distance_km = Column(Integer, nullable=True)
    duration_min = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    trips = relationship("Trip", back_populates="route")


class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    seat_layout_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    seats = relationship("Seat", back_populates="bus", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="bus")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("bus_id", "seat_no", name="uq_seat_bus_seatno"),)

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id", ondelete="CASCADE"), nullable=False, index=True)
    seat_no = Column(String, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    bus = relationship("Bus", back_populates="seats")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False, index=True)
    departure_time = Column(String, nullable=False, index=True)  # ISO string for MVP
    price = Column(Numeric(10, 2), nullable=False)
    status = Column(String, nullable=False, default="scheduled")
    created_at = Column(DateTime, server_default=func.current_timestamp())

    route = relationship("Route", back_populates="trips")
    bus = relationship("Bus", back_populates="trips")
    bookings = relationship("Booking", back_populates="trip")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_ref = Column(String, nullable=False, unique=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, index=True)
    passenger_name = Column(String, nullable=False)
    passenger_email = Column(String, nullable=False)
    passenger_phone = Column(String, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, nullable=False, default="confirmed")
    created_at = Column(DateTime, server_default=func.current_timestamp())

    trip = relationship("Trip", back_populates="bookings")
    seats = relationship("BookingSeat", back_populates="booking", cascade="all, delete-orphan")


class BookingSeat(Base):
    __tablename__ = "booking_seats"
    __table_args__ = (
        UniqueConstraint("booking_id", "seat_id", name="uq_booking_seat"),
        UniqueConstraint("seat_id", name="uq_seat_once"),
    )

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    booking = relationship("Booking", back_populates="seats")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)  # MVP only
    created_at = Column(DateTime, server_default=func.current_timestamp())

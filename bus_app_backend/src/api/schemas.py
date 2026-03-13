"""Pydantic models (schemas) for Bus Booking MVP API."""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class RouteOut(BaseModel):
    id: int
    origin: str
    destination: str
    distance_km: Optional[int] = None
    duration_min: Optional[int] = None


class BusOut(BaseModel):
    id: int
    code: str
    name: str
    seat_layout_json: Optional[str] = None


class SeatOut(BaseModel):
    id: int
    seat_no: str
    is_active: int


class TripOut(BaseModel):
    id: int
    departure_time: str
    price: Decimal
    status: str
    route: RouteOut
    bus: BusOut


class TripSearchResponse(BaseModel):
    trips: List[TripOut]


class SeatAvailabilityResponse(BaseModel):
    trip_id: int
    bus_id: int
    seats: List[SeatOut]
    booked_seat_ids: List[int]


class BookingCreateRequest(BaseModel):
    trip_id: int = Field(..., description="Trip id being booked")
    seat_ids: List[int] = Field(..., min_length=1, description="List of seat ids to book")
    passenger_name: str = Field(..., min_length=2, description="Passenger full name")
    passenger_email: str = Field(..., min_length=3, description="Passenger email")
    passenger_phone: Optional[str] = Field(None, description="Passenger phone")


class BookingOut(BaseModel):
    id: int
    booking_ref: str
    trip_id: int
    passenger_name: str
    passenger_email: str
    passenger_phone: Optional[str] = None
    total_amount: Decimal
    status: str
    seat_ids: List[int]


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str = Field(..., description="MVP admin token (static bearer token)")


class AdminRouteCreate(BaseModel):
    origin: str
    destination: str
    distance_km: Optional[int] = None
    duration_min: Optional[int] = None


class AdminBusCreate(BaseModel):
    code: str
    name: str
    seat_layout_json: Optional[str] = None


class AdminTripCreate(BaseModel):
    route_id: int
    bus_id: int
    departure_time: str = Field(..., description="ISO timestamp string")
    price: Decimal
    status: str = Field("scheduled", description="scheduled/cancelled")

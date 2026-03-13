"""FastAPI routers for Bus Booking MVP."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.api.admin_auth import require_admin
from src.api.db import get_db
from src.api.models import Booking, BookingSeat, Bus, Route, Seat, Trip
from src.api.schemas import (
    AdminBusCreate,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminRouteCreate,
    AdminTripCreate,
    BookingCreateRequest,
    BookingOut,
    BusOut,
    RouteOut,
    SeatAvailabilityResponse,
    SeatOut,
    TripOut,
    TripSearchResponse,
)
from src.api.services import create_booking

public_router = APIRouter(prefix="/api", tags=["Public"])
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


@public_router.get(
    "/routes",
    summary="List routes",
    description="List all routes available for browsing/search.",
    response_model=List[RouteOut],
    operation_id="list_routes",
)
def list_routes(db: Session = Depends(get_db)) -> List[RouteOut]:
    routes = db.execute(select(Route).order_by(Route.origin, Route.destination)).scalars().all()
    return [RouteOut.model_validate(r.__dict__) for r in routes]


@public_router.get(
    "/trips",
    summary="Search trips",
    description="Search trips by optional origin, destination. Returns upcoming trips.",
    response_model=TripSearchResponse,
    operation_id="search_trips",
)
def search_trips(
    origin: Optional[str] = Query(default=None),
    destination: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> TripSearchResponse:
    stmt = (
        select(Trip)
        .options(joinedload(Trip.route), joinedload(Trip.bus))
        .where(Trip.status == "scheduled")
        .order_by(Trip.departure_time)
    )
    if origin:
        stmt = stmt.where(Trip.route.has(Route.origin.ilike(f"%{origin}%")))
    if destination:
        stmt = stmt.where(Trip.route.has(Route.destination.ilike(f"%{destination}%")))

    trips = db.execute(stmt).scalars().all()
    out = []
    for t in trips:
        out.append(
            TripOut(
                id=t.id,
                departure_time=t.departure_time,
                price=t.price,
                status=t.status,
                route=RouteOut(
                    id=t.route.id,
                    origin=t.route.origin,
                    destination=t.route.destination,
                    distance_km=t.route.distance_km,
                    duration_min=t.route.duration_min,
                ),
                bus=BusOut(id=t.bus.id, code=t.bus.code, name=t.bus.name, seat_layout_json=t.bus.seat_layout_json),
            )
        )
    return TripSearchResponse(trips=out)


@public_router.get(
    "/trips/{trip_id}/seats",
    summary="Seat availability",
    description="Returns all seats for a trip's bus plus currently booked seat ids.",
    response_model=SeatAvailabilityResponse,
    operation_id="trip_seat_availability",
)
def trip_seat_availability(trip_id: int, db: Session = Depends(get_db)) -> SeatAvailabilityResponse:
    trip = db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    seats = db.execute(select(Seat).where(Seat.bus_id == trip.bus_id).order_by(Seat.seat_no)).scalars().all()
    booked = db.execute(
        select(BookingSeat.seat_id)
        .join(Booking, BookingSeat.booking_id == Booking.id)
        .where(Booking.trip_id == trip_id)
        .where(Booking.status == "confirmed")
    ).scalars().all()

    return SeatAvailabilityResponse(
        trip_id=trip_id,
        bus_id=trip.bus_id,
        seats=[SeatOut(id=s.id, seat_no=s.seat_no, is_active=s.is_active) for s in seats],
        booked_seat_ids=list(booked),
    )


@public_router.post(
    "/bookings",
    summary="Create booking",
    description="Books selected seats on a trip for a passenger. Returns booking reference for confirmation.",
    response_model=BookingOut,
    operation_id="create_booking",
)
def create_booking_endpoint(payload: BookingCreateRequest, db: Session = Depends(get_db)) -> BookingOut:
    booking = create_booking(
        db=db,
        trip_id=payload.trip_id,
        seat_ids=payload.seat_ids,
        passenger_name=payload.passenger_name,
        passenger_email=payload.passenger_email,
        passenger_phone=payload.passenger_phone,
    )

    seat_ids = [bs.seat_id for bs in booking.seats]
    return BookingOut(
        id=booking.id,
        booking_ref=booking.booking_ref,
        trip_id=booking.trip_id,
        passenger_name=booking.passenger_name,
        passenger_email=booking.passenger_email,
        passenger_phone=booking.passenger_phone,
        total_amount=booking.total_amount,
        status=booking.status,
        seat_ids=seat_ids,
    )


@public_router.get(
    "/bookings/{booking_ref}",
    summary="Get booking",
    description="Fetch booking confirmation details by booking reference.",
    response_model=BookingOut,
    operation_id="get_booking",
)
def get_booking(booking_ref: str, db: Session = Depends(get_db)) -> BookingOut:
    booking = db.execute(select(Booking).where(Booking.booking_ref == booking_ref)).scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    seat_ids = db.execute(select(BookingSeat.seat_id).where(BookingSeat.booking_id == booking.id)).scalars().all()
    return BookingOut(
        id=booking.id,
        booking_ref=booking.booking_ref,
        trip_id=booking.trip_id,
        passenger_name=booking.passenger_name,
        passenger_email=booking.passenger_email,
        passenger_phone=booking.passenger_phone,
        total_amount=booking.total_amount,
        status=booking.status,
        seat_ids=list(seat_ids),
    )


@admin_router.post(
    "/login",
    summary="Admin login (MVP)",
    description="Validates username/password from admin_users and returns a static bearer token for MVP.",
    response_model=AdminLoginResponse,
    operation_id="admin_login",
)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> AdminLoginResponse:
    from src.api.models import AdminUser  # local import avoids circulars

    user = db.execute(
        select(AdminUser).where(AdminUser.username == payload.username, AdminUser.password == payload.password)
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # token handled by require_admin
    import os

    token = os.getenv("ADMIN_TOKEN", "dev-admin-token")
    return AdminLoginResponse(token=token)


@admin_router.get(
    "/routes",
    summary="Admin list routes",
    description="List routes (admin).",
    response_model=List[RouteOut],
    operation_id="admin_list_routes",
)
def admin_list_routes(_: object = Depends(require_admin), db: Session = Depends(get_db)) -> List[RouteOut]:
    routes = db.execute(select(Route).order_by(Route.id.desc())).scalars().all()
    return [RouteOut(id=r.id, origin=r.origin, destination=r.destination, distance_km=r.distance_km, duration_min=r.duration_min) for r in routes]


@admin_router.post(
    "/routes",
    summary="Admin create route",
    description="Create a route (admin).",
    response_model=RouteOut,
    operation_id="admin_create_route",
)
def admin_create_route(payload: AdminRouteCreate, _: object = Depends(require_admin), db: Session = Depends(get_db)) -> RouteOut:
    r = Route(
        origin=payload.origin,
        destination=payload.destination,
        distance_km=payload.distance_km,
        duration_min=payload.duration_min,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return RouteOut(id=r.id, origin=r.origin, destination=r.destination, distance_km=r.distance_km, duration_min=r.duration_min)


@admin_router.get(
    "/buses",
    summary="Admin list buses",
    description="List buses (admin).",
    response_model=List[BusOut],
    operation_id="admin_list_buses",
)
def admin_list_buses(_: object = Depends(require_admin), db: Session = Depends(get_db)) -> List[BusOut]:
    buses = db.execute(select(Bus).order_by(Bus.id.desc())).scalars().all()
    return [BusOut(id=b.id, code=b.code, name=b.name, seat_layout_json=b.seat_layout_json) for b in buses]


@admin_router.post(
    "/buses",
    summary="Admin create bus",
    description="Create a bus with a seat layout (admin).",
    response_model=BusOut,
    operation_id="admin_create_bus",
)
def admin_create_bus(payload: AdminBusCreate, _: object = Depends(require_admin), db: Session = Depends(get_db)) -> BusOut:
    b = Bus(code=payload.code, name=payload.name, seat_layout_json=payload.seat_layout_json)
    db.add(b)
    db.commit()
    db.refresh(b)
    return BusOut(id=b.id, code=b.code, name=b.name, seat_layout_json=b.seat_layout_json)


@admin_router.post(
    "/trips",
    summary="Admin create trip",
    description="Create a trip (admin).",
    response_model=TripOut,
    operation_id="admin_create_trip",
)
def admin_create_trip(payload: AdminTripCreate, _: object = Depends(require_admin), db: Session = Depends(get_db)) -> TripOut:
    route = db.get(Route, payload.route_id)
    bus = db.get(Bus, payload.bus_id)
    if not route or not bus:
        raise HTTPException(status_code=400, detail="Invalid route_id or bus_id")

    t = Trip(
        route_id=payload.route_id,
        bus_id=payload.bus_id,
        departure_time=payload.departure_time,
        price=payload.price,
        status=payload.status,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    return TripOut(
        id=t.id,
        departure_time=t.departure_time,
        price=t.price,
        status=t.status,
        route=RouteOut(id=route.id, origin=route.origin, destination=route.destination, distance_km=route.distance_km, duration_min=route.duration_min),
        bus=BusOut(id=bus.id, code=bus.code, name=bus.name, seat_layout_json=bus.seat_layout_json),
    )

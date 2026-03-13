"""Service-layer helpers for Bus Booking MVP."""
from __future__ import annotations

import secrets
from decimal import Decimal
from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api import models


def _generate_booking_ref() -> str:
    # short, user-friendly reference
    return f"BK-{secrets.token_hex(4).upper()}"


# PUBLIC_INTERFACE
def create_booking(
    db: Session,
    trip_id: int,
    seat_ids: List[int],
    passenger_name: str,
    passenger_email: str,
    passenger_phone: str | None,
) -> models.Booking:
    """
    Create a booking atomically, preventing double booking of a seat.

    Raises:
      HTTPException(409) if any seat is already booked.
      HTTPException(400/404) for invalid inputs.
    """
    trip = db.get(models.Trip, trip_id)
    if not trip or trip.status != "scheduled":
        raise HTTPException(status_code=404, detail="Trip not found or not bookable")

    # Validate seats belong to the trip's bus
    seats = db.execute(
        select(models.Seat).where(models.Seat.id.in_(seat_ids))
    ).scalars().all()
    if len(seats) != len(set(seat_ids)):
        raise HTTPException(status_code=400, detail="One or more seats are invalid")

    for s in seats:
        if s.bus_id != trip.bus_id:
            raise HTTPException(status_code=400, detail="One or more seats do not belong to this trip's bus")
        if s.is_active != 1:
            raise HTTPException(status_code=400, detail="One or more seats are not active")

    total_amount = (Decimal(str(trip.price)) * Decimal(len(seat_ids))).quantize(Decimal("0.01"))
    booking = models.Booking(
        booking_ref=_generate_booking_ref(),
        trip_id=trip_id,
        passenger_name=passenger_name,
        passenger_email=passenger_email,
        passenger_phone=passenger_phone,
        total_amount=total_amount,
        status="confirmed",
    )

    try:
        db.add(booking)
        db.flush()  # get booking.id

        for seat_id in seat_ids:
            db.add(models.BookingSeat(booking_id=booking.id, seat_id=seat_id))

        db.commit()
        db.refresh(booking)
        return booking
    except IntegrityError:
        db.rollback()
        # Most likely seat unique constraint violated
        raise HTTPException(status_code=409, detail="One or more seats are already booked")

# FILE: app/services/subscription_validator.py
"""
Subscription validation service - ensures bookings are only made for hostels with active subscriptions.
"""
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.operations import Subscription


class SubscriptionValidator:
    """Validate hostel subscription status for bookings."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def validate_hostel_subscription(
        self, 
        hostel_id: str, 
        check_in_date: date | None = None,
        check_out_date: date | None = None
    ) -> bool:
        """
        Validate that hostel has an active subscription for the given dates.
        
        Args:
            hostel_id: UUID of the hostel
            check_in_date: Optional check-in date (defaults to today)
            check_out_date: Optional check-out date
        
        Returns:
            True if subscription is valid
        
        Raises:
            HTTPException if subscription is invalid
        """
        # Get active subscription for this hostel
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.hostel_id == hostel_id,
                Subscription.status == "active"
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Hostel does not have an active subscription. Please contact the administrator."
            )
        
        today = date.today()
        start_date = subscription.start_date
        end_date = subscription.end_date
        
        # Check if subscription is active overall
        if today < start_date:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Hostel subscription starts on {start_date.isoformat()}. Bookings are not yet available."
            )
        
        if today > end_date:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Hostel subscription expired on {end_date.isoformat()}. Please renew to accept new bookings."
            )
        
        # If booking dates are provided, check if they fall within subscription period
        if check_in_date and check_out_date:
            if check_in_date < start_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Check-in date {check_in_date.isoformat()} is before subscription start date {start_date.isoformat()}. "
                           f"Bookings are only allowed from {start_date.isoformat()} onwards."
                )
            
            if check_in_date > end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Check-in date {check_in_date.isoformat()} is after subscription expiry {end_date.isoformat()}. "
                           f"Bookings are only allowed until {end_date.isoformat()}."
                )
            
            if check_out_date > end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Check-out date {check_out_date.isoformat()} exceeds subscription expiry {end_date.isoformat()}. "
                           f"Stay must end by {end_date.isoformat()}."
                )
        
        return True
    
    async def get_subscription_info(self, hostel_id: str) -> dict | None:
        """Get subscription information for a hostel."""
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.hostel_id == hostel_id,
                Subscription.status == "active"
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return None
        
        today = date.today()
        return {
            "has_active_subscription": True,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "is_active": subscription.start_date <= today <= subscription.end_date,
            "days_remaining": max(0, (subscription.end_date - today).days),
            "tier": subscription.tier,
            "auto_renew": subscription.auto_renew,
        }
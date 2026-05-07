from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import Response
from datetime import date, timedelta 
import re
from sqlalchemy import select
from app.models.user import User, UserRole
from uuid import uuid4
from datetime import UTC, datetime


from app.dependencies import CurrentUser, require_roles
from app.dependencies import DBSession
from app.models.hostel import HostelStatus
from app.schemas.super_admin import (
    AssignHostelRequest,
    SuperAdminProfileResponse,
    SuperAdminProfileUpdateRequest,
    ValidatePasswordRequest,
    PasswordValidationResponse,
    AssignHostelsRequest,
    ChangePasswordRequest,
    SuperAdminHostelListResponse,
    SuperAdminHostelRejectRequest,
    SuperAdminAdminCreateRequest,
    SuperAdminAdminResponse,
    SuperAdminDashboardResponse,
    SuperAdminHostelCreateRequest,
    SuperAdminHostelResponse,
    SuperAdminSubscriptionResponse,
    SuperAdminSubscriptionCreateRequest,
    SuperAdminSubscriptionUpdateRequest,
    SuperAdminSubscriptionDetailResponse,
)
from app.services.super_admin_service import SuperAdminService
from app.schemas.student import CompleteStudentDetailResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


router = APIRouter()
SuperAdmin = Annotated[CurrentUser, Depends(require_roles("super_admin"))]


def validate_email(email: str) -> bool:
    """
    Validate email format and domain.
    
    Checks:
    - Valid email format (contains @ and .)
    - Domain has at least one dot after @
    - No spaces
    """
    email = email.strip()
    
    # Check for empty
    if not email:
        return False
    
    # Check for spaces
    if ' ' in email:
        return False
    
    # Check for @ symbol
    if '@' not in email:
        return False
    
    # Split into local and domain parts
    local_part, domain_part = email.rsplit('@', 1)
    
    # Check local part is not empty
    if not local_part:
        return False
    
    # Check domain has at least one dot and not empty
    if not domain_part or '.' not in domain_part:
        return False
    
    # Check domain doesn't start or end with dot
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    
    # Check for valid characters (basic check)
    # Allow letters, numbers, dots, hyphens, underscores in local part
    valid_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(valid_pattern, email))


@router.get("/dashboard", response_model=SuperAdminDashboardResponse)
async def dashboard(_: SuperAdmin, db: DBSession):
    """**Platform overview** — total hostels, admins, and active subscriptions."""
    return await SuperAdminService(db).get_dashboard()


@router.get("/hostels", response_model=list[SuperAdminHostelResponse])
async def list_hostels(_: SuperAdmin, db: DBSession):
    """**List all hostels** across the platform in all statuses."""
    return await SuperAdminService(db).list_hostels()


@router.get("/hostels/paginated", response_model=SuperAdminHostelListResponse)
async def list_hostels_paginated(
    _: SuperAdmin,
    db: DBSession,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
):
    """Spec-compatible paginated hostel list with optional status filter."""
    return await SuperAdminService(db).list_hostels_paginated(status=status, page=page, per_page=per_page)


@router.get("/hostels/{hostel_id}", response_model=SuperAdminHostelResponse)
async def get_hostel(hostel_id: str, _: SuperAdmin, db: DBSession):
    return await SuperAdminService(db).get_hostel(hostel_id)


@router.post("/hostels", response_model=SuperAdminHostelResponse, status_code=201)
async def create_hostel(payload: SuperAdminHostelCreateRequest, _: SuperAdmin, db: DBSession):
    """**Create a new hostel.** Created in `pending_approval` status by default."""
    return await SuperAdminService(db).create_hostel(payload)


@router.post("/hostels/{hostel_id}/images", status_code=201)
async def add_hostel_images(_: SuperAdmin, hostel_id: str, db: DBSession, payload: list[dict]):
    """**Add images to a hostel.** Each item: {url, thumbnail_url?, caption?, is_primary?}"""
    from app.models.hostel import HostelImage
    from sqlalchemy import select
    from app.models.hostel import Hostel
    result = await db.execute(select(Hostel).where(Hostel.id == hostel_id))
    hostel = result.scalar_one_or_none()
    if hostel is None:
        raise HTTPException(status_code=404, detail="Hostel not found.")
    added = []
    for i, img in enumerate(payload[:10]):
        url = img.get("url", "").strip()
        if not url:
            continue
        image = HostelImage(
            hostel_id=hostel_id,
            url=url,
            thumbnail_url=img.get("thumbnail_url", url),
            caption=img.get("caption"),
            image_type=img.get("image_type", "gallery"),
            sort_order=i,
            is_primary=(i == 0 and img.get("is_primary", True)),
        )
        db.add(image)
        added.append({"url": url, "sort_order": i})
    await db.commit()
    return {"hostel_id": hostel_id, "images_added": len(added)}


@router.patch("/hostels/{hostel_id}/approve", response_model=SuperAdminHostelResponse)
async def approve_hostel(hostel_id: str, _: SuperAdmin, db: DBSession):
    """**Approve a hostel** — sets status to `active`, making it publicly visible."""
    return await SuperAdminService(db).update_hostel_status(hostel_id, HostelStatus.ACTIVE)


@router.patch("/hostels/{hostel_id}/reject", response_model=SuperAdminHostelResponse)
async def reject_hostel(hostel_id: str, _: SuperAdmin, db: DBSession):
    """**Reject a hostel** — sets status to `rejected`. Hostel will not appear publicly."""
    return await SuperAdminService(db).update_hostel_status(hostel_id, HostelStatus.REJECTED)


@router.post("/hostels/{hostel_id}/approve", response_model=SuperAdminHostelResponse)
async def approve_hostel_post(hostel_id: str, _: SuperAdmin, db: DBSession):
    return await SuperAdminService(db).update_hostel_status(hostel_id, HostelStatus.ACTIVE)


@router.post("/hostels/{hostel_id}/reject", response_model=SuperAdminHostelResponse)
async def reject_hostel_post(hostel_id: str, payload: SuperAdminHostelRejectRequest, _: SuperAdmin, db: DBSession):
    _ = payload.reason  # reason accepted for contract; model currently has no rejection_reason field.
    return await SuperAdminService(db).update_hostel_status(hostel_id, HostelStatus.REJECTED)


@router.post("/hostels/{hostel_id}/suspend", response_model=SuperAdminHostelResponse)
async def suspend_hostel_post(hostel_id: str, _: SuperAdmin, db: DBSession):
    return await SuperAdminService(db).update_hostel_status(hostel_id, HostelStatus.SUSPENDED)


@router.patch("/hostels/{hostel_id}/suspend", response_model=SuperAdminHostelResponse)
async def suspend_hostel(hostel_id: str, _: SuperAdmin, db: DBSession):
    """**Suspend a hostel** — temporarily removes it from public listing."""
    return await SuperAdminService(db).update_hostel_status(hostel_id, HostelStatus.SUSPENDED)


@router.get("/admins", response_model=list[SuperAdminAdminResponse])
async def list_admins(_: SuperAdmin, db: DBSession):
    """**List all hostel admins** on the platform."""
    return await SuperAdminService(db).list_admins()


@router.post("/admins", response_model=SuperAdminAdminResponse, status_code=201)
async def create_admin(payload: SuperAdminAdminCreateRequest, _: SuperAdmin, db: DBSession):
    """
    **Create a new hostel admin account.**
    
    The created user gets role `hostel_admin`. Use `assign-hostels` next
    to give them access to specific hostels.
    
    Requirements:
    - Email must be valid format (e.g., user@example.com)
    - Phone must be 10 digits (Indian format) or 10-15 digits international
    - Password must be at least 8 chars with uppercase, lowercase, and number
    - Full name must be at least 2 characters
    """
    from app.core.security import hash_password
    from app.models.user import User, UserRole
    from sqlalchemy import select
    import re
    
    # Normalize email (lowercase)
    normalized_email = payload.email.lower().strip()
    
    # Check if email already exists
    existing_email = await db.execute(
        select(User).where(User.email == normalized_email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{payload.email}' is already registered."
        )
    
    # Normalize phone: remove all non-digit characters
    # Keep only digits for storage and checking
    normalized_phone = re.sub(r'[^0-9]', '', payload.phone)
    
    # For Indian numbers, ensure 10 digits
    # Check if phone is Indian number (starts with 91 or +91)
    # If it's an international format, keep as is after cleaning
    if normalized_phone.startswith('91') and len(normalized_phone) == 12:
        normalized_phone = normalized_phone[2:]  # Remove 91 prefix
    elif normalized_phone.startswith('0'):
        normalized_phone = normalized_phone[1:]  # Remove leading 0
    
    # Validate phone length
    if len(normalized_phone) < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Phone number must be at least 10 digits"
        )
    if len(normalized_phone) > 15:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Phone number must be at most 15 digits"
        )
    
    # For Indian numbers (10 digits), validate they start with 6-9
    if len(normalized_phone) == 10 and not normalized_phone[0] in ['6', '7', '8', '9']:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Indian phone number must start with 6, 7, 8, or 9"
        )
    
    # Check if phone already exists
    existing_phone = await db.execute(
        select(User).where(User.phone == normalized_phone)
    )
    if existing_phone.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Phone number '{payload.phone}' is already registered."
        )
    
    # Validate password
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters"
        )
    if not re.search(r'[A-Z]', payload.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one uppercase letter"
        )
    if not re.search(r'[a-z]', payload.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one lowercase letter"
        )
    if not re.search(r'[0-9]', payload.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one number"
        )
    
    # Create admin user with normalized phone
    admin = User(
        email=normalized_email,
        phone=normalized_phone,  # Store only digits
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=UserRole.HOSTEL_ADMIN,
        is_active=True,
        is_email_verified=True,
        is_phone_verified=True,
    )
    
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    
    return admin

@router.post("/admins/{admin_id}/assign-hostels")
async def assign_hostels(
    admin_id: str, 
    payload: AssignHostelsRequest, 
    current_user: SuperAdmin, 
    db: DBSession
):
    """
    **Assign hostels to an admin.**

    Replaces existing assignments. Pass an array of `hostel_ids`.
    The admin will only be able to manage the assigned hostels.
    """
    from app.models.hostel import AdminHostelMapping, Hostel
    from sqlalchemy import select, delete
    
    # Verify admin exists
    result = await db.execute(
        select(User).where(User.id == admin_id, User.role == UserRole.HOSTEL_ADMIN)
    )
    admin_user = result.scalar_one_or_none()
    
    if admin_user is None:
        raise HTTPException(status_code=404, detail="Admin not found.")
    
    # Delete existing assignments
    await db.execute(
        delete(AdminHostelMapping).where(AdminHostelMapping.admin_id == admin_id)
    )
    
    # Create new assignments
    for index, hostel_id in enumerate(payload.hostel_ids):
        # Verify hostel exists
        hostel_result = await db.execute(select(Hostel).where(Hostel.id == hostel_id))
        if hostel_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail=f"Hostel {hostel_id} not found.")
        
        mapping = AdminHostelMapping(
            id=uuid4(),
            admin_id=admin_id,
            hostel_id=hostel_id,
            is_primary=(index == 0),
            assigned_by=current_user.id,
            assigned_at=datetime.now(UTC)
        )
        db.add(mapping)
    
    await db.commit()
    return {"admin_id": admin_id, "hostel_ids": payload.hostel_ids}

@router.post("/admins/{admin_id}/assign-hostel")
async def assign_hostel(admin_id: str, payload: AssignHostelRequest, current_user: SuperAdmin, db: DBSession):
    return await SuperAdminService(db).assign_hostel(
        actor_id=current_user.id,
        admin_id=admin_id,
        payload=payload,
    )


# ==================== SUBSCRIPTION ENDPOINTS ====================


@router.get("/subscriptions", response_model=list[SuperAdminSubscriptionDetailResponse])
async def list_subscriptions(
    _: SuperAdmin,
    db: DBSession,
    status_filter: str | None = Query(None, description="Filter by status: active, expired, cancelled"),
    hostel_id: str | None = Query(None, description="Filter by hostel ID"),
    hostel_name: str | None = Query(None, description="Filter by hostel name (partial match)"),
    start_date_from: date | None = Query(None, description="Subscription start date from (YYYY-MM-DD)"),
    start_date_to: date | None = Query(None, description="Subscription start date to (YYYY-MM-DD)"),
    end_date_from: date | None = Query(None, description="Subscription end date from (YYYY-MM-DD)"),
    end_date_to: date | None = Query(None, description="Subscription end date to (YYYY-MM-DD)"),
):
    """
    **List all hostel subscriptions with advanced filtering.**
    
    Optional filters:
    - `status_filter`: active, expired, cancelled
    - `hostel_id`: Filter by specific hostel ID
    - `hostel_name`: Filter by hostel name (partial match, case-insensitive)
    - `start_date_from`: Subscriptions starting on or after this date
    - `start_date_to`: Subscriptions starting on or before this date
    - `end_date_from`: Subscriptions ending on or after this date
    - `end_date_to`: Subscriptions ending on or before this date
    """
    from sqlalchemy import select, func
    from app.models.operations import Subscription
    from app.models.hostel import Hostel
    from datetime import date as date_type
    
    # Start with base query
    query = select(Subscription)
    
    # Apply filters
    if status_filter:
        query = query.where(Subscription.status == status_filter)
    
    if hostel_id:
        query = query.where(Subscription.hostel_id == hostel_id)
    
    # Handle hostel_name filter - we need to join with hostels table
    if hostel_name:
        query = query.join(Hostel, Subscription.hostel_id == Hostel.id)
        # Use ILIKE for case-insensitive partial matching
        query = query.where(Hostel.name.ilike(f"%{hostel_name}%"))
    
    # Date range filters
    if start_date_from:
        query = query.where(Subscription.start_date >= start_date_from)
    if start_date_to:
        query = query.where(Subscription.start_date <= start_date_to)
    if end_date_from:
        query = query.where(Subscription.end_date >= end_date_from)
    if end_date_to:
        query = query.where(Subscription.end_date <= end_date_to)
    
    # Order by creation date
    query = query.order_by(Subscription.created_at.desc())
    
    result = await db.execute(query)
    subscriptions = list(result.scalars().all())
    
    # Get hostel names in bulk (avoid N+1 query)
    hostel_ids_list = list(set(str(sub.hostel_id) for sub in subscriptions))
    hostel_names_dict = {}
    if hostel_ids_list:
        hostel_result = await db.execute(
            select(Hostel.id, Hostel.name).where(Hostel.id.in_(hostel_ids_list))
        )
        hostel_names_dict = {str(row.id): row.name for row in hostel_result.all()}
    
    today = date_type.today()
    response = []
    for sub in subscriptions:
        days_remaining = None
        if sub.status == "active" and sub.end_date:
            days_remaining = (sub.end_date - today).days
            days_remaining = max(0, days_remaining)
        
        response.append({
            "id": str(sub.id),
            "hostel_id": str(sub.hostel_id),
            "hostel_name": hostel_names_dict.get(str(sub.hostel_id)),
            "tier": sub.tier,
            "price_monthly": float(sub.price_monthly),
            "start_date": sub.start_date.isoformat(),
            "end_date": sub.end_date.isoformat(),
            "status": sub.status,
            "auto_renew": sub.auto_renew,
            "days_remaining": days_remaining,
            "created_at": sub.created_at,
            "updated_at": sub.updated_at,
        })
    
    return response


@router.get("/subscriptions/{subscription_id}", response_model=SuperAdminSubscriptionDetailResponse)
async def get_subscription(
    subscription_id: str,
    _: SuperAdmin,
    db: DBSession,
):
    """
    **Get a single subscription by ID.**
    
    Returns detailed subscription information including days remaining.
    """
    from sqlalchemy import select
    from app.models.operations import Subscription
    from app.models.hostel import Hostel
    from datetime import date
    
    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with id '{subscription_id}' not found."
        )
    
    hostel_result = await db.execute(
        select(Hostel).where(Hostel.id == subscription.hostel_id)
    )
    hostel = hostel_result.scalar_one_or_none()
    
    days_remaining = None
    if subscription.status == "active" and subscription.end_date:
        days_remaining = (subscription.end_date - date.today()).days
        days_remaining = max(0, days_remaining)
    
    return {
        "id": str(subscription.id),
        "hostel_id": str(subscription.hostel_id),
        "hostel_name": hostel.name if hostel else None,
        "tier": subscription.tier,
        "price_monthly": float(subscription.price_monthly),
        "start_date": subscription.start_date.isoformat(),
        "end_date": subscription.end_date.isoformat(),
        "status": subscription.status,
        "auto_renew": subscription.auto_renew,
        "days_remaining": days_remaining,
        "created_at": subscription.created_at,
        "updated_at": subscription.updated_at,
    }


@router.post("/subscriptions", response_model=SuperAdminSubscriptionDetailResponse, status_code=201)
async def create_subscription(
    payload: SuperAdminSubscriptionCreateRequest,
    _: SuperAdmin,
    db: DBSession,
):
    """
    **Create a new subscription for a hostel.**
    
    Validates:
    - Hostel exists
    - No overlapping active subscription exists
    - End date is after start date
    
    Subscription tiers: `basic`, `standard`, `professional`, `enterprise`
    Status can be: `active`, `expired`, `cancelled`
    """
    return await SuperAdminService(db).create_subscription(payload)


@router.patch("/subscriptions/{subscription_id}", response_model=SuperAdminSubscriptionDetailResponse)
async def update_subscription(
    subscription_id: str,
    payload: SuperAdminSubscriptionUpdateRequest,
    _: SuperAdmin,
    db: DBSession,
):
    """
    **Update an existing subscription.**
    
    All fields are optional. Can update:
    - tier, price_monthly, start_date, end_date
    - auto_renew flag
    - status (active, expired, cancelled)
    
    Active subscriptions cannot be deleted, but can be cancelled (status: cancelled).
    """
    return await SuperAdminService(db).update_subscription(subscription_id, payload)


@router.post("/subscriptions/{subscription_id}/cancel", response_model=dict)
async def cancel_subscription(
    subscription_id: str,
    _: SuperAdmin,
    db: DBSession,
):
    """
    **Cancel an active subscription.**
    
    Changes status to 'cancelled' and disables auto-renew.
    This is a soft cancel - the subscription record remains for audit purposes.
    """
    return await SuperAdminService(db).cancel_subscription(subscription_id)

@router.get("/subscriptions/stats")
async def get_subscription_stats(
    _: SuperAdmin,
    db: DBSession,
):
    """
    **Get subscription statistics for dashboard.**
    
    Returns:
    - Total subscriptions count
    - Active subscriptions count
    - Expiring soon (next 30 days)
    - Revenue summary
    - Distribution by tier
    """
    from sqlalchemy import func
    from app.models.operations import Subscription
    from datetime import date, timedelta
    
    today = date.today()
    next_30_days = today + timedelta(days=30)
    
    # Basic counts
    total_result = await db.execute(select(func.count()).select_from(Subscription))
    total = int(total_result.scalar() or 0)
    
    active_result = await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.status == "active")
    )
    active = int(active_result.scalar() or 0)
    
    expired_result = await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.status == "expired")
    )
    expired = int(expired_result.scalar() or 0)
    
    cancelled_result = await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.status == "cancelled")
    )
    cancelled = int(cancelled_result.scalar() or 0)
    
    # Expiring soon
    expiring_soon_result = await db.execute(
        select(func.count())
        .select_from(Subscription)
        .where(
            Subscription.status == "active",
            Subscription.end_date <= next_30_days,
            Subscription.end_date >= today
        )
    )
    expiring_soon = int(expiring_soon_result.scalar() or 0)
    
    # Monthly recurring revenue
    revenue_result = await db.execute(
        select(func.sum(Subscription.price_monthly))
        .where(Subscription.status == "active")
    )
    monthly_recurring_revenue = float(revenue_result.scalar() or 0)
    
    # Distribution by tier
    tier_result = await db.execute(
        select(Subscription.tier, func.count())
        .where(Subscription.status == "active")
        .group_by(Subscription.tier)
    )
    tier_distribution = {tier: count for tier, count in tier_result.all()}
    
    return {
        "total_subscriptions": total,
        "active_subscriptions": active,
        "expired_subscriptions": expired,
        "cancelled_subscriptions": cancelled,
        "expiring_soon": expiring_soon,
        "monthly_recurring_revenue": monthly_recurring_revenue,
        "tier_distribution": tier_distribution,
    }

    
@router.get("/subscriptions/search/hostels")
async def search_hostels_for_subscriptions(
    _: SuperAdmin,
    db: DBSession,
    q: str = Query(..., min_length=2, description="Search query for hostel name"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
):
    """
    **Search hostels by name for subscription filtering.**
    
    Returns matching hostels with their subscription status.
    Useful for building autocomplete dropdowns in the frontend.
    """
    from sqlalchemy import select
    from app.models.hostel import Hostel
    from app.models.operations import Subscription
    
    # Search hostels
    result = await db.execute(
        select(Hostel.id, Hostel.name, Hostel.city, Hostel.status)
        .where(Hostel.name.ilike(f"%{q}%"))
        .order_by(Hostel.name)
        .limit(limit)
    )
    hostels = result.all()
    
    # Get subscription status for each hostel
    response = []
    for hostel in hostels:
        # Check if hostel has active subscription
        sub_result = await db.execute(
            select(Subscription)
            .where(
                Subscription.hostel_id == str(hostel.id),
                Subscription.status == "active"
            )
            .limit(1)
        )
        has_active_sub = sub_result.scalar_one_or_none() is not None
        
        # Also get the latest subscription if exists
        latest_sub_result = await db.execute(
            select(Subscription)
            .where(Subscription.hostel_id == str(hostel.id))
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        latest_sub = latest_sub_result.scalar_one_or_none()
        
        response.append({
            "id": str(hostel.id),
            "name": hostel.name,
            "city": hostel.city,
            "hostel_status": hostel.status.value if hasattr(hostel.status, "value") else str(hostel.status),
            "has_active_subscription": has_active_sub,
            "current_tier": latest_sub.tier if latest_sub else None,
            "subscription_status": latest_sub.status if latest_sub else None,
        })
    
    return response

@router.delete("/subscriptions/{subscription_id}", status_code=204)
async def delete_subscription(
    subscription_id: str,
    _: SuperAdmin,
    db: DBSession,
):
    """
    **Delete a subscription.**
    
    Only allowed for cancelled or expired subscriptions.
    Active subscriptions must be cancelled first.
    """
    await SuperAdminService(db).delete_subscription(subscription_id)
    return Response(status_code=204)





@router.get("/students", response_model=list[CompleteStudentDetailResponse])
async def list_all_students(
    _: SuperAdmin,
    db: DBSession,
    page: int = 1,
    per_page: int = 20,
    hostel_id: str | None = None,
    status: str | None = None,
):
    """
    Super Admin endpoint to list all students with complete details.
    Supports filtering by hostel_id and status.
    """
    return await SuperAdminService(db).list_all_students(
        page=page, 
        per_page=per_page,
        hostel_id=hostel_id,
        status=status
    )


@router.get("/students/{student_id}", response_model=CompleteStudentDetailResponse)
async def get_student_details(
    student_id: str,
    _: SuperAdmin,
    db: DBSession,
):
    """Super Admin endpoint to get complete student details by ID."""
    student = await SuperAdminService(db).get_complete_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@router.get("/students/{student_id}/payments")
async def get_student_payments(
    student_id: str,
    _: SuperAdmin,
    db: DBSession,
):
    """Get payment history for a student."""
    return await SuperAdminService(db).get_student_payments(student_id)

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: SuperAdmin,
    db: DBSession
):
    """Change super admin password."""
    from app.core.security import verify_password, hash_password
    from app.repositories.user_repository import UserRepository
    from datetime import UTC, datetime
    from sqlalchemy import select
    from app.models.user import User
    
    # Validate passwords match
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")
    
    # Get user
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Verify old password
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect current password.")
    
    # Update password
    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    
    # Optional: Revoke all other sessions
    repo = UserRepository(db)
    await repo.revoke_all_refresh_tokens(
        user_id=current_user.id,
        revoked_at=datetime.now(UTC)
    )
    
    return {"message": "Password changed successfully."}



@router.get("/profile", response_model=SuperAdminProfileResponse)
async def get_profile(current_user: SuperAdmin, db: DBSession):
    """Get super admin profile."""
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

@router.patch("/profile", response_model=SuperAdminProfileResponse)
async def update_profile(
    payload: SuperAdminProfileUpdateRequest,
    current_user: SuperAdmin,
    db: DBSession
):
    """Update super admin profile."""
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if payload.full_name:
        user.full_name = payload.full_name
    if payload.phone:
        # Check phone uniqueness
        existing = await db.execute(
            select(User).where(User.phone == payload.phone, User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Phone already in use.")
        user.phone = payload.phone
    if payload.profile_picture_url is not None:
        user.profile_picture_url = payload.profile_picture_url
    
    await db.commit()
    await db.refresh(user)
    return user




def validate_password_strength(password: str) -> list[str]:
    """Validate password strength and return list of errors."""
    import re
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return errors

@router.post("/validate-password", response_model=PasswordValidationResponse)
async def validate_password(payload: ValidatePasswordRequest):
    """Validate password strength without changing it."""
    errors = validate_password_strength(payload.password)
    return PasswordValidationResponse(
        is_valid=len(errors) == 0,
        errors=errors
    )
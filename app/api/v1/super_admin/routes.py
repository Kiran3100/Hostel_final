from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response

from app.dependencies import CurrentUser, require_roles
from app.dependencies import DBSession
from app.models.hostel import HostelStatus
from app.schemas.super_admin import (
    AssignHostelRequest,
    AssignHostelsRequest,
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


router = APIRouter()
SuperAdmin = Annotated[CurrentUser, Depends(require_roles("super_admin"))]


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
    """
    return await SuperAdminService(db).create_admin(payload)


@router.post("/admins/{admin_id}/assign-hostels")
async def assign_hostels(admin_id: str, payload: AssignHostelsRequest, current_user: SuperAdmin, db: DBSession):
    """
    **Assign hostels to an admin.**

    Replaces existing assignments. Pass an array of `hostel_ids`.
    The admin will only be able to manage the assigned hostels.
    """
    return await SuperAdminService(db).assign_hostels(actor_id=current_user.id, admin_id=admin_id, payload=payload)


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
):
    """
    **List all hostel subscriptions.**
    
    Optional filters:
    - `status_filter`: active, expired, cancelled
    - `hostel_id`: Filter by specific hostel
    
    Returns detailed information including hostel name and days remaining.
    """
    from sqlalchemy import select
    from app.models.operations import Subscription
    from app.models.hostel import Hostel
    from datetime import date
    
    query = select(Subscription)
    
    if status_filter:
        query = query.where(Subscription.status == status_filter)
    if hostel_id:
        query = query.where(Subscription.hostel_id == hostel_id)
    
    query = query.order_by(Subscription.created_at.desc())
    result = await db.execute(query)
    subscriptions = list(result.scalars().all())
    
    # Get hostel names in bulk
    hostel_ids = list(set(str(sub.hostel_id) for sub in subscriptions))
    hostel_result = await db.execute(
        select(Hostel.id, Hostel.name).where(Hostel.id.in_(hostel_ids))
    )
    hostel_names = {str(row.id): row.name for row in hostel_result.all()}
    
    today = date.today()
    response = []
    for sub in subscriptions:
        days_remaining = None
        if sub.status == "active" and sub.end_date:
            days_remaining = (sub.end_date - today).days
            days_remaining = max(0, days_remaining)
        
        response.append({
            "id": str(sub.id),
            "hostel_id": str(sub.hostel_id),
            "hostel_name": hostel_names.get(str(sub.hostel_id)),
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
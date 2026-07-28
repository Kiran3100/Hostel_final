import logging
from typing import Dict, Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt, decrypt
from app.models.hostel import HostelPaymentConfig
from app.schemas.payment_config import HostelPaymentConfigUpdate

logger = logging.getLogger(__name__)

class PaymentConfigService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_payment_config(self, hostel_id: str) -> dict:
        """Returns the config without exposing secrets (for the frontend)."""
        result = await self.session.execute(
            select(HostelPaymentConfig).where(HostelPaymentConfig.hostel_id == hostel_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            return {
                "hostel_id": hostel_id,
                "is_configured": False,
                "is_active": False,
                "razorpay_key_id": None,
                "razorpay_linked_account_id": None,
                "platform_fee_percentage": 0.0,
                "payment_mode": "unconfigured",
            }
            
        payment_mode = "route" if config.razorpay_linked_account_id else "direct"
        return {
            "hostel_id": str(config.hostel_id),
            "razorpay_key_id": config.razorpay_key_id,
            "razorpay_linked_account_id": config.razorpay_linked_account_id,
            "platform_fee_percentage": config.platform_fee_percentage or 0.0,
            "payment_mode": payment_mode,
            "is_active": config.is_active,
            "is_configured": True,
        }

    async def upsert_payment_config(self, hostel_id: str, payload: HostelPaymentConfigUpdate) -> dict:
        """Create or update payment configuration. Supports both direct keys and Razorpay Route."""
        # Validate: must provide either direct keys OR a linked account ID
        using_route = bool(payload.razorpay_linked_account_id)
        using_direct = bool(payload.razorpay_key_id)

        if not using_route and not using_direct:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either razorpay_key_id (direct integration) or razorpay_linked_account_id (Razorpay Route)."
            )

        if using_direct and payload.razorpay_key_id and not payload.razorpay_key_id.startswith("rzp_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Razorpay Key ID must start with rzp_live_ or rzp_test_"
            )

        if using_route and payload.razorpay_linked_account_id and not payload.razorpay_linked_account_id.startswith("acc_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Razorpay Linked Account ID must start with acc_"
            )
            
        result = await self.session.execute(
            select(HostelPaymentConfig).where(HostelPaymentConfig.hostel_id == hostel_id)
        )
        config = result.scalar_one_or_none()
        
        if config:
            # Update existing
            config.is_active = payload.is_active
            if using_direct:
                config.razorpay_key_id = payload.razorpay_key_id
                config.razorpay_linked_account_id = None  # Switch back to direct
                config.platform_fee_percentage = 0.0
                if payload.razorpay_key_secret:
                    config.razorpay_key_secret_encrypted = encrypt(payload.razorpay_key_secret)
                if payload.razorpay_webhook_secret is not None:
                    config.razorpay_webhook_secret_encrypted = encrypt(payload.razorpay_webhook_secret) if payload.razorpay_webhook_secret else None
            if using_route:
                config.razorpay_linked_account_id = payload.razorpay_linked_account_id
                config.platform_fee_percentage = payload.platform_fee_percentage or 0.0
                # Keep any existing direct keys in case admin wants to switch back
        else:
            # Create new
            if using_direct and not payload.razorpay_key_secret:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Razorpay Key Secret is required for initial direct configuration."
                )
            config = HostelPaymentConfig(
                hostel_id=hostel_id,
                razorpay_key_id=payload.razorpay_key_id if using_direct else None,
                razorpay_key_secret_encrypted=encrypt(payload.razorpay_key_secret) if (using_direct and payload.razorpay_key_secret) else None,
                razorpay_webhook_secret_encrypted=encrypt(payload.razorpay_webhook_secret) if payload.razorpay_webhook_secret else None,
                razorpay_linked_account_id=payload.razorpay_linked_account_id if using_route else None,
                platform_fee_percentage=payload.platform_fee_percentage or 0.0,
                is_active=payload.is_active
            )
            self.session.add(config)
            
        await self.session.commit()
        
        payment_mode = "route" if config.razorpay_linked_account_id else "direct"
        return {
            "hostel_id": str(config.hostel_id),
            "razorpay_key_id": config.razorpay_key_id,
            "razorpay_linked_account_id": config.razorpay_linked_account_id,
            "platform_fee_percentage": config.platform_fee_percentage or 0.0,
            "payment_mode": payment_mode,
            "is_active": config.is_active,
            "is_configured": True,
        }

    async def get_decrypted_keys(self, hostel_id: str) -> dict | None:
        """
        Internal use only: returns decrypted keys for creating Razorpay orders.
        Returns a dict with:
          - key_id, key_secret, webhook_secret: for direct integration
          - linked_account_id, platform_fee_percentage: for Razorpay Route split payments
          - mode: 'direct' or 'route'
        """
        result = await self.session.execute(
            select(HostelPaymentConfig).where(HostelPaymentConfig.hostel_id == hostel_id)
        )
        config = result.scalar_one_or_none()
        
        if not config or not config.is_active:
            return None

        # ── Razorpay Route mode ───────────────────────────────────────────────
        if config.razorpay_linked_account_id:
            return {
                "mode": "route",
                "linked_account_id": config.razorpay_linked_account_id,
                "platform_fee_percentage": config.platform_fee_percentage or 0.0,
                # Route uses Super Admin's master keys from .env (set in RazorpayClient defaults)
                "key_id": None,
                "key_secret": None,
                "webhook_secret": None,
            }
            
        # ── Direct integration mode ───────────────────────────────────────────
        if not config.razorpay_key_secret_encrypted:
            return None
        try:
            return {
                "mode": "direct",
                "key_id": config.razorpay_key_id,
                "key_secret": decrypt(config.razorpay_key_secret_encrypted),
                "webhook_secret": decrypt(config.razorpay_webhook_secret_encrypted) if config.razorpay_webhook_secret_encrypted else None,
                "linked_account_id": None,
                "platform_fee_percentage": 0.0,
            }
        except Exception as e:
            logger.error(f"Failed to decrypt Razorpay keys for hostel {hostel_id}: {e}")
            return None

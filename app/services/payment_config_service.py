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
                "is_configured": False,
                "is_active": False
            }
            
        return {
            "hostel_id": config.hostel_id,
            "razorpay_key_id": config.razorpay_key_id,
            "is_active": config.is_active,
            "is_configured": True
        }

    async def upsert_payment_config(self, hostel_id: str, payload: HostelPaymentConfigUpdate) -> dict:
        """Create or update payment configuration."""
        if not payload.razorpay_key_id.startswith("rzp_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Razorpay Key ID must start with rzp_live_ or rzp_test_"
            )
            
        result = await self.session.execute(
            select(HostelPaymentConfig).where(HostelPaymentConfig.hostel_id == hostel_id)
        )
        config = result.scalar_one_or_none()
        
        if config:
            # Update existing
            config.razorpay_key_id = payload.razorpay_key_id
            config.is_active = payload.is_active
            if payload.razorpay_key_secret:
                config.razorpay_key_secret_encrypted = encrypt(payload.razorpay_key_secret)
            if payload.razorpay_webhook_secret is not None:
                config.razorpay_webhook_secret_encrypted = encrypt(payload.razorpay_webhook_secret) if payload.razorpay_webhook_secret else None
        else:
            # Create new
            if not payload.razorpay_key_secret:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Razorpay Key Secret is required for initial configuration."
                )
            config = HostelPaymentConfig(
                hostel_id=hostel_id,
                razorpay_key_id=payload.razorpay_key_id,
                razorpay_key_secret_encrypted=encrypt(payload.razorpay_key_secret),
                razorpay_webhook_secret_encrypted=encrypt(payload.razorpay_webhook_secret) if payload.razorpay_webhook_secret else None,
                is_active=payload.is_active
            )
            self.session.add(config)
            
        await self.session.commit()
        
        return {
            "message": "Payment configuration saved successfully.",
            "hostel_id": config.hostel_id,
            "razorpay_key_id": config.razorpay_key_id,
            "is_active": config.is_active,
            "is_configured": True
        }

    async def get_decrypted_keys(self, hostel_id: str) -> Dict[str, Any] | None:
        """Internal use only: returns decrypted keys for creating orders."""
        result = await self.session.execute(
            select(HostelPaymentConfig).where(HostelPaymentConfig.hostel_id == hostel_id)
        )
        config = result.scalar_one_or_none()
        
        if not config or not config.is_active:
            return None
            
        try:
            return {
                "key_id": config.razorpay_key_id,
                "key_secret": decrypt(config.razorpay_key_secret_encrypted),
                "webhook_secret": decrypt(config.razorpay_webhook_secret_encrypted) if config.razorpay_webhook_secret_encrypted else None
            }
        except Exception as e:
            logger.error(f"Failed to decrypt Razorpay keys for hostel {hostel_id}: {e}")
            return None

"""
Test email service functionality.
Run with: python scripts/test_email.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.integrations.email import EmailService


async def test_all_emails():
    """Test all email templates."""
    email_service = EmailService()
    
    print("\n" + "="*60)
    print("📧 Testing StayEase Email Service")
    print("="*60 + "\n")
    
    # Use your test email here - CHANGE THIS TO YOUR EMAIL!
    test_email = "test@example.com"  # 👈 REPLACE WITH YOUR ACTUAL EMAIL
    
    tests = [
        {
            "name": "Booking Confirmation",
            "func": email_service.send_booking_confirmation,
            "kwargs": {
                "recipient_email": test_email,
                "recipient_name": "John Doe",
                "booking_number": "BK-TEST-001",
                "hostel_name": "Green Valley Hostel",
                "check_in_date": "2026-04-01",
                "check_out_date": "2026-04-15",
                "total_amount": 15000.00,
                "payment_status": "paid"
            }
        },
        {
            "name": "Payment Receipt",
            "func": email_service.send_payment_receipt,
            "kwargs": {
                "recipient_email": test_email,
                "recipient_name": "John Doe",
                "payment_id": "pay_test_001",
                "amount": 15000.00,
                "payment_type": "booking_advance",
                "transaction_id": "txn_001",
                "payment_date": "2026-03-27"
            }
        },
        {
            "name": "Password Reset OTP",
            "func": email_service.send_password_reset_otp,
            "kwargs": {
                "recipient_email": test_email,
                "recipient_name": "John Doe",
                "otp": "123456"
            }
        },
        {
            "name": "Welcome Email",
            "func": email_service.send_registration_welcome,
            "kwargs": {
                "recipient_email": test_email,
                "recipient_name": "John Doe"
            }
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests, 1):
        print(f"[{i}/4] Testing: {test['name']}")
        try:
            await test['func'](**test['kwargs'])
            print(f"         ✅ SUCCESS - Email sent to {test_email}")
            passed += 1
        except Exception as e:
            print(f"         ❌ FAILED - {str(e)}")
            failed += 1
        print()
    
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 All emails sent successfully!")
        print(f"Check your inbox at: {test_email}")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        print("Common issues:")
        print("  - SMTP credentials not configured in .env")
        print("  - Using regular password instead of App Password")
        print("  - Firewall blocking SMTP connection")
        print("  - Invalid email address")
    
    print()


if __name__ == "__main__":
    print("\nStarting email service tests...\n")
    asyncio.run(test_all_emails())

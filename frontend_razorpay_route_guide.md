# Frontend Integration Guide — Razorpay Route Split Payments

> **Document Version:** 1.0  
> **Backend Status:** ✅ Live on Production (Render)  
> **Date:** 28 July 2026  
> **Author:** Backend Team  
> **For:** Frontend Team

---

## 📌 Overview

Our platform has been upgraded to support **Razorpay Route (Split Payments)** — Option 3 of our payment architecture.

Under this model, when a student pays rent:

```
Student pays ₹10,000
        │
        ▼
  Razorpay Gateway (Super Admin Master Account)
        │
        ├──► 5% Platform Fee (₹500) ──► Super Admin Bank Account
        │
        └──► 95% Rent (₹9,500)     ──► Hostel Admin Bank Account (instantly)
```

This replaces the need for manual payouts to hostel owners. Razorpay handles the split in real-time at the moment of payment.

---

## 🏗️ Architecture — How it works end to end

### Mode 1: Direct Integration (Current / Existing)
- Each hostel provides their own Razorpay API Keys.
- Student payments go directly into the Hostel Admin's Razorpay account.
- Super Admin earns nothing from student payments.
- `payment_mode = "direct"`

### Mode 2: Razorpay Route (New)
- Super Admin holds the **Master Razorpay Account**.
- Each Hostel Admin gets a **Linked Account** under the Master Account (after KYC).
- All student payments go through the Master Account.
- Razorpay **automatically splits** the amount based on our configured `platform_fee_percentage`.
- `payment_mode = "route"`

---

## 🔄 Full Payment Workflow

### Step 1 — Hostel Onboarding (One-time setup by Super Admin)
1. Hostel Admin completes KYC on Razorpay (bank account, PAN, business docs).
2. Razorpay issues a **Linked Account ID** (format: `acc_XXXXXXXXXX`).
3. Super Admin saves this on our platform via the API.

### Step 2 — Student Initiates Payment
1. Student opens the booking/payment screen on the frontend app.
2. Frontend calls `POST /api/v1/payments/booking/{booking_id}/pay`.
3. **Backend automatically detects** whether the hostel uses `"direct"` or `"route"` mode.
4. If `"route"`: Backend uses Super Admin Razorpay keys + attaches a `transfers` object instructing Razorpay how to split.
5. Backend returns a `razorpay_order` object (same structure as before — no frontend changes needed here).

### Step 3 — Student Completes Payment
1. Frontend opens the Razorpay checkout modal using the `razorpay_order.key_id` and `razorpay_order.id` (same as current flow).
2. Student pays using UPI / Card / NetBanking.
3. Razorpay **instantly** splits:
   - Platform fee % → Super Admin account
   - Remaining % → Hostel Linked Account

### Step 4 — Payment Verification (No change)
1. Frontend calls `POST /api/v1/payments/verify` with `razorpay_payment_id`, `razorpay_order_id`, `razorpay_signature`.
2. Backend verifies and marks the booking as paid.

---

## 📋 What Frontend Team Needs to Build

> [!IMPORTANT]
> Only the **Admin Dashboard** needs changes. The student-facing payment flow is completely unchanged.

---

### 1. Payment Config Settings Page (Admin Dashboard)

This is the most important UI change. Currently the settings page only shows fields for "Direct Razorpay Keys". You need to add a toggle/tab to switch between modes.

#### UI Design Suggestion

```
┌─────────────────────────────────────────────────────────┐
│  💳 Payment Configuration                               │
│                                                         │
│  Payment Mode:                                          │
│  ○ Direct Integration   ● Razorpay Route (Split)        │
│                                                         │
│  ── Razorpay Route Settings ───────────────────────     │
│  Linked Account ID:  [ acc_XXXXXXXXXX          ]        │
│  Platform Fee (%):   [ 5                       ]        │
│                      (You keep 5%, hostel gets 95%)     │
│                                                         │
│  [ Save Configuration ]                                 │
└─────────────────────────────────────────────────────────┘
```

#### API Call to Save Route Config

```http
PUT /api/v1/admin/payment-config?hostel_id={hostel_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "razorpay_linked_account_id": "acc_XXXXXXXXXX",
  "platform_fee_percentage": 5.0,
  "is_active": true
}
```

#### API Call to Save Direct Config (existing, unchanged)

```http
PUT /api/v1/admin/payment-config?hostel_id={hostel_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "razorpay_key_id": "rzp_live_XXXXXXXXXX",
  "razorpay_key_secret": "YYYYYYYY",
  "is_active": true
}
```

---

### 2. Display Payment Mode Badge

The `GET /api/v1/admin/payment-config?hostel_id={hostel_id}` response now includes new fields. Use them to display the current configuration clearly.

#### Updated API Response Schema

```json
{
  "hostel_id": "uuid-string",
  "is_active": true,
  "is_configured": true,
  "razorpay_key_id": "rzp_live_xxx",
  "razorpay_linked_account_id": "acc_xxx",
  "platform_fee_percentage": 5.0,
  "payment_mode": "route"
}
```

| Field | Type | Description |
|---|---|---|
| `payment_mode` | `"direct"` \| `"route"` \| `"unconfigured"` | Current active payment mode |
| `razorpay_linked_account_id` | `string \| null` | Linked Account ID if using Route mode |
| `platform_fee_percentage` | `float` | % of each payment kept by Super Admin |

#### UI Badge Suggestion

```jsx
// Show this badge on the payment settings card
{config.payment_mode === "route" && (
  <Badge color="green">✅ Split Payments (Razorpay Route)</Badge>
)}
{config.payment_mode === "direct" && (
  <Badge color="blue">💳 Direct Integration</Badge>
)}
{config.payment_mode === "unconfigured" && (
  <Badge color="red">⚠️ Not Configured</Badge>
)}
```

---

### 3. Validation Rules (Frontend)

When saving Route mode config, validate before calling the API:

| Field | Validation Rule |
|---|---|
| `razorpay_linked_account_id` | Must start with `acc_` |
| `platform_fee_percentage` | Must be a number between `0` and `100` |
| `is_active` | Boolean, default `true` |

When saving Direct mode config:

| Field | Validation Rule |
|---|---|
| `razorpay_key_id` | Must start with `rzp_live_` or `rzp_test_` |
| `razorpay_key_secret` | Required on first save, optional on update |

---

## 🙅 What Frontend Does NOT Need to Change

| Area | Status |
|---|---|
| Student checkout / Razorpay modal | ✅ No change |
| Payment verification API call | ✅ No change |
| Booking payment flow | ✅ No change |
| Remaining balance payment | ✅ No change |
| Webhook handling | ✅ No change |
| Invoice / Billing history | ✅ No change |

---

## 🧪 Testing Checklist for Frontend Team

After building the UI, verify the following:

- [ ] Admin can view current `payment_mode` on the settings page
- [ ] Admin can switch from Direct → Route by entering `acc_` ID and fee %
- [ ] Admin can switch back from Route → Direct by entering `rzp_` keys
- [ ] Validation prevents saving `acc_` prefix check fails
- [ ] Badge correctly shows `"route"`, `"direct"`, or `"unconfigured"`
- [ ] Student payment flow still works normally (no visual change)

---

## ❓ FAQ

**Q: What is a Linked Account ID?**  
A: It is a unique ID (`acc_XXXXXXXXXX`) issued by Razorpay after a hostel owner completes their KYC (bank account + PAN verification). The Super Admin collects this from Razorpay dashboard and enters it in our platform.

**Q: Does the student know about the split?**  
A: No. The student only sees the total amount (e.g., ₹10,000). Razorpay handles the split silently in the background.

**Q: What if a hostel doesn't have a Linked Account yet?**  
A: They continue using Direct Integration (their own Razorpay keys). The two modes are fully independent and can coexist across different hostels.

**Q: Who sets the platform fee percentage?**  
A: The Super Admin sets it per hostel when saving the Linked Account ID.

---

## 📞 Contact

For any questions on API responses or backend behavior, contact the backend team.  
All APIs are documented on Swagger: `https://hostel-final-cqes.onrender.com/docs`

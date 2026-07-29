# Proposal: Manual UPI QR Code Payments for Hostel Rent

This document outlines a proposal to introduce **Static UPI QR Code payments** for hostel rent. This allows Hostel Admins to receive rent directly into their bank accounts with **0% transaction fees** and **zero KYC setup**, while keeping the Super Admin's Razorpay integration active purely for SaaS subscriptions.

---

## 📌 The Concept

```
┌────────────────────────────────────────────────────────┐
│                      Levitica Nestora                  │
├───────────────────────────┬────────────────────────────┤
│   SaaS Subscriptions      │     Student Rent payments  │
│   (Super Admin Revenue)   │     (Hostel Admin Income)  │
├───────────────────────────┼────────────────────────────┤
│  💳 Razorpay (Automated)  │  📱 Static UPI QR Code      │
│  • Fee: 2% + GST          │  • Fee: 0%                 │
│  • Automated Capture      │  • Manual Admin Approval   │
└───────────────────────────┴────────────────────────────┘
```

---

## ⚖️ Razorpay vs. Static QR Codes

| Feature | 💳 Razorpay Direct Key | 📱 Static UPI QR Code |
| :--- | :--- | :--- |
| **Transaction Charges** | 2% + GST (paid to Razorpay) | **0% (100% Free)** |
| **Onboarding KYC** | Strict business docs + bank review | **Instant (Just upload a QR code image)** |
| **Payment Capturing** | Fully automated (webhook confirms) | Manual verification of UTR / Screenshot |
| **Confirmation Speed** | Instant (< 5 seconds) | Depends on Admin approval speed |
| **Fraud Risk** | 0% (Secure & automated) | Low-Medium (Requires admin to verify) |

---

## 🔄 Step-by-Step Payment Workflow

To implement this, the backend and frontend will follow this 4-step workflow:

### Step 1: Hostel Admin Setup (Settings Page)
Instead of entering Razorpay API keys, the Hostel Admin configures their manual payment details in the settings panel:
1. **Uploads QR Code Image:** (Saved to Cloudinary via backend).
2. **Inputs UPI ID:** (e.g., `hostelname@okaxis`).
3. **Inputs Bank Details (Optional):** Account Number, Holder Name, and IFSC code for direct IMPS/NEFT transfers.

---

### Step 2: Student Payment Checkout (Frontend)
When the student goes to pay the booking advance or remaining rent:
1. The app displays the **Hostel's QR Code Image** and **UPI ID**.
2. The student copies the UPI ID or scans the QR code using any app (GPay, PhonePe, Paytm, BHIM).
3. The student completes the transfer inside their payment app.

---

### Step 3: Student Submits Proof (Frontend -> Backend)
Because static QR payments are not linked to an API, the student must manually verify they paid:
1. Student takes a **screenshot** of the success screen from their payment app.
2. In the Nestora app, they upload the screenshot image.
3. They enter the **12-digit UPI Reference Number / UTR Number** (e.g., `329812345678`).
4. They click "Submit Proof". The status of the booking moves to `payment_verification_pending`.

---

### Step 4: Admin Verification & Approval (Admin Panel)
1. The Hostel Admin logs in and goes to the **Pending Payments** tab.
2. They see a list of submissions containing:
   - Student Name
   - Amount Paid
   - UTR Number
   - Link to Screenshot
3. The Admin checks their bank account (via PhonePe Business or Bank App) to confirm receipt of the money.
4. If matched, the Admin clicks **"Approve"**. The booking becomes `PAID`, and the bed is confirmed.

---

## 🖥️ UI / UX Layout Suggestions for Frontend

### A. Settings Page (Hostel Admin)
Add a toggle/tab: **[● Bank Transfer / UPI QR]**
* Input: UPI ID
* File Upload: Dropzone to upload GPay/PhonePe business QR code.
* Input: Account Holder Name, Bank Account Number, IFSC.

### B. Payment Screen (Student Mobile App)
```
┌──────────────────────────────────────────────────┐
│ Pay Booking Advance: ₹5,000                      │
├──────────────────────────────────────────────────┤
│                                                  │
│   [ QR Code Image (GPay/PhonePe) ]               │
│                                                  │
│   UPI ID: sunrisehostel@okaxis   [Copy]          │
│                                                  │
├──────────────────────────────────────────────────┤
│ 📂 Upload Payment Screenshot                     │
│ [ Choose Image... ]                              │
│                                                  │
│ ✍️ Enter 12-Digit UTR / UPI Ref No.              │
│ [ 329812345678 ]                                 │
│                                                  │
│ [ Submit Payment Proof ]                         │
└──────────────────────────────────────────────────┘
```

### C. Approvals Dashboard (Hostel Admin)
* Display a table of all pending reviews.
* Add a modal showing the uploaded screenshot and UTR number side-by-side with an **Approve** and **Reject** button.

---

## 💡 Frontend Developer Summary

1. **New UI Screens to Build:**
   * QR upload form on Settings Page.
   * Proof upload form (Image picker + UTR input) on student checkout.
   * "Pending Payments Verification" list and review modal in Admin dashboard.
2. **API Logic:**
   * Upload payment proof screenshots using the existing `/api/v1/public/upload` endpoint.
   * Submit transaction details (`utr`, `screenshot_url`) to backend.

# Razorpay Route Implementation Guide (Split Payments)

## 📌 Overview
This document outlines the implementation strategy for **Option 3: Split Payments** using [Razorpay Route](https://razorpay.com/route/). 

In our SaaS + Marketplace business model, students pay rent/fees through the platform. Using Razorpay Route, we can automatically split a single payment from a student so that:
1. Our **Platform Fee** goes directly to our Master Account (Super Admin).
2. The **Remaining Amount (Rent)** goes instantly to the specific Hostel's bank account (Hostel Admin).

### Why use Razorpay Route?
- **Compliance & Legal:** Removes the legal and tax liabilities of holding funds that belong to the hostels.
- **Automated Payouts:** Hostels receive their money directly and instantly without manual reconciliation on our end.
- **Trust:** Hostel owners don't have to wait for us to process manual payouts.

---

## 🛠 Backend Team Responsibilities

The backend team will act as the orchestrator of the split payment logic.

### 1. Onboarding & Linked Accounts
Before a hostel can receive split payments, they need a "Linked Account" under our Master Razorpay Account.
- Create an API endpoint to accept KYC details (Bank Account, IFSC, PAN, Business Details) from the Hostel Admin.
- Call the Razorpay API (`POST /route/accounts`) to create a Linked Account.
- Save the returned `account_id` (e.g., `acc_xyz123`) in our database, mapped to the `Hostel` entity.

### 2. Modifying Order Creation (The Split Logic)
When a student initiates a payment, the backend currently generates a standard Razorpay Order. This needs to be updated.
- Calculate the split amounts dynamically. For example, if rent is ₹10,000 and our platform fee is 5%:
  - Platform Fee: ₹500
  - Hostel Amount: ₹9,500
- Add the `transfers` array to the Razorpay Create Order payload. 
- Instruct Razorpay to transfer ₹9,500 to the hostel's `account_id` and keep the remaining ₹500 in the Master Account.

### 3. Webhooks & Edge Cases
- **Refunds:** Implement logic to handle refunds. If a student cancels, the backend must trigger a refund that accurately pulls money back from the Linked Account.
- **Webhooks:** Listen to Route-specific webhooks (e.g., `transfer.processed`, `transfer.failed`) to keep our database in sync with actual settlement statuses.

---

## 💻 Frontend Team Responsibilities

The frontend effort is split between the Student App and the Hostel Admin Dashboard.

### 1. Student Checkout Experience
- **Impact: ZERO.** 
- The student checkout experience remains exactly the same. They will see a total amount of ₹10,000, and the Razorpay modal will open normally. The splitting happens entirely on the backend and Razorpay's servers.

### 2. Hostel Admin Dashboard: KYC Onboarding
To receive payments, Hostel Admins must provide their bank details.
- **Option A (Custom UI):** Build forms to collect Bank Account Number, IFSC code, PAN, and Aadhaar/Business Registration. Send this data to the backend.
- **Option B (Hosted Onboarding - Recommended):** Rely on Razorpay's Hosted Onboarding. The frontend simply adds an "Activate Payments" button that redirects the Hostel Admin to a secure Razorpay URL to fill out their details, then redirects them back to our dashboard when complete.

### 3. Hostel Admin Dashboard: Earnings View (Optional but recommended)
- Build a "Settlements & Payouts" page where Hostel Admins can view a breakdown of payments they have received, minus platform fees, and check when funds were deposited into their bank accounts.

---

## 🚀 Next Steps for Implementation
1. **Business/Product:** Decide on the exact platform fee structure (percentage vs. flat fee).
2. **Backend:** Generate test API keys for Razorpay Route and create a test Linked Account.
3. **Frontend:** Evaluate whether to build a custom KYC flow or use Razorpay Hosted Onboarding.

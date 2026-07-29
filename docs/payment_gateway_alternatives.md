# Payment Gateway Alternatives Comparison Guide

This document compares alternative payment gateways to Razorpay for the **Levitica Nestora** platform. It analyzes transaction charges, developer integration complexity, onboarding requirements, and pros/cons for both Super Admin and Hostel Admins.

---

## 📊 Summary Comparison

| Payment Gateway | Standard Transaction Charges | Onboarding / KYC Speed | Developer Integration Ease | Best Suited For |
| :--- | :--- | :--- | :--- | :--- |
| **Razorpay** *(Current)* | **2.0%** + GST | 🟠 Medium (1-3 days) | 🟠 Medium (Custom Modal) | Comprehensive Indian payment suite |
| **Stripe India** | **2.0% - 3.0%** + GST | 🔴 Hard (Strict business checks) | 🟢 Easy (Stripe Hosted Checkout) | SaaS platforms looking for clean code |
| **PhonePe PG** | **1.8% - 2.0%** + GST (UPI is often cheaper) | 🟢 Easy (Fast verification) | 🟢 Easy (Hosted redirect redirect) | Heavy UPI transactions (India) |
| **Cashfree** | **1.9%** + GST | 🟢 Easy (Friendly to small merchants) | 🟢 Easy (Hosted JS web SDK) | Fast onboarding & reliable Indian API |

---

## 1. Razorpay (Current System)
Razorpay is India's leading payment gateway but can feel complicated because of its strict compliance and frontend modal script setup.

### 💳 Transaction Charges
* **UPI & RuPay Debit Cards:** 2.0% per transaction (plus 18% GST).
* **Credit Cards & Netbanking:** 2.0% per transaction (plus 18% GST).
* **International / Diners / Amex Cards:** 3.0% per transaction (plus 18% GST).

### ⚙️ Developer Integration (Frontend)
* Uses a Javascript SDK modal (`window.Razorpay`) that opens over the app. 
* Requires frontend state management to prevent double-payments if the user closes the modal.

---

## 2. Stripe India (Easiest Integration)
Stripe has the best developer documentation and cleanest API design in the software industry. 

### 💳 Transaction Charges
* **Indian Cards, Netbanking & UPI:** 2.0% per transaction (plus 18% GST).
* **International Cards:** 4.3% per transaction (plus 18% GST).
* **Setup/Annual Maintenance Fees:** ₹0 (Free).

### 👍 Why it is easier:
* **Stripe Checkout:** Developers do not need to build or design payment modals. The frontend simply redirects the student to a secure, mobile-responsive page hosted entirely on Stripe's servers. 
* Once the payment is complete, Stripe automatically redirects the student back to your website.

### ⚠️ The Catch for India:
* Due to RBI rules, Stripe India has strict onboarding regulations. Hostel Admins must have registered businesses (LLP, Private Limited, or registered Sole Proprietorship) with a GSTIN. Individual/personal savings accounts are rarely accepted.

---

## 3. PhonePe PG (Best for India & UPI)
PhonePe is backed by Walmart and is the most popular consumer UPI app in India. Their merchant payment gateway has very high success rates for UPI transactions.

### 💳 Transaction Charges
* **UPI Transactions:** Often promotional at **0% to 1.5%** depending on volume.
* **Standard Debit/Credit Cards & Netbanking:** **1.8%** per transaction (plus 18% GST).

### 👍 Why it is easier:
* **Instant Brand Recognition:** Every Indian student has PhonePe, Google Pay, or Paytm on their phone.
* **PhonePe SDK:** Simple API that redirects the user directly to the PhonePe app or UPI app on their mobile phone, making mobile checkout take less than 10 seconds.
* **Onboarding:** Super easy. Most hostel owners in India already use PhonePe Business, making KYC approval fast.

---

## 4. Cashfree Payments (Fastest Onboarding)
Cashfree is a direct competitor to Razorpay. It is highly popular among startups and education/hostel platforms in India because of its developer-friendly checkout flows.

### 💳 Transaction Charges
* **UPI, Debit Cards & Netbanking:** **1.9%** per transaction (plus 18% GST).
* **Credit Cards:** 1.9% per transaction (plus 18% GST).

### 👍 Why it is easier:
* **Hosted Web Checkout:** Just like Stripe, Cashfree offers a hosted checkout page. The frontend team doesn't need to load external JavaScript packages or modals into their React/Next.js code.
* **Admin-Friendly:** Cashfree's merchant dashboard is simple, and their customer support generally approves KYC accounts faster than Razorpay.

---

## 📋 Document Requirements for Hostel Admins (All Gateways)

Regardless of the gateway chosen, the Hostel Admin must provide these basic documents to start accepting online payments under Indian law:

1. **PAN Card** (Business PAN or Individual PAN if Proprietorship).
2. **Aadhaar Card** of the business owner.
3. **Cancel Check** or Bank Account Statement (where rent money will be sent).
4. **Business Address Proof** (Rent agreement, electricity bill, or GST certificate).

---

## 💡 Final Suggestion for the Team

If the frontend team wants to change because Razorpay is "complicated", they should look at **Cashfree Hosted Checkout** or **PhonePe PG**. 

These two offer:
1. **No payment modals to build** (hosted page redirect flow).
2. **Simplified onboarding** for Indian hostel owners.
3. **Cheaper transaction rates** for UPI payments.

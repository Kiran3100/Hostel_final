# 🏨 Student Hostel Transfer — Feature Specification


## 📌 Overview

A student currently enrolled in one hostel can request to **switch/transfer to another hostel**. 

There are **2 types of transfers**, and the rules are different for each:

---

## 🔀 Transfer Type 1 — Internal Transfer (Same Admin, Different Hostel)

> **Example:** Admin Rahul owns Hostel A and Hostel B. Student wants to move from Hostel A → Hostel B.

### ✅ Rules

| Rule | Detail |
|---|---|
| Who can request? | Student |
| Who approves? | The same hostel admin (only 1 admin needed) |
| Approval steps | 1 step only — Admin approves |
| Data access after transfer | Admin has **FULL ACCESS** to all old and new data |
| Old booking | Marked as `completed` or `cancelled` |
| New booking | Created fresh in the new hostel |

### 🔁 Transfer Flow (Step by Step)

```
Student requests transfer to Admin's other hostel
        ↓
Admin reviews the request
        ↓
Admin approves with one click
        ↓
Old booking → marked as COMPLETED/CANCELLED
New booking → created in new hostel
Student profile → updated to new hostel
        ↓
✅ Transfer Complete
```

### 📂 Data Visibility (Internal Transfer)

| Data Type | Old Hostel | New Hostel |
|---|---|---|
| Student Profile | ✅ Full Access | ✅ Full Access |
| Old Payments & Invoices | ✅ Full Access | ✅ Full Access |
| New Payments & Invoices | ✅ Full Access | ✅ Full Access |
| Documents (ID proof, photo) | ✅ Full Access | ✅ Full Access |
| Complaints (old) | ✅ Full Access | ✅ Full Access |
| Attendance Records | ✅ Full Access | ✅ Full Access |

> **Reason:** Same admin owns both hostels, so there are no privacy restrictions.

---

## 🔀 Transfer Type 2 — External Transfer (Different Admin, Different Hostel)

> **Example:** Student is in Admin Rahul's Hostel A. Student wants to move to Admin Priya's Hostel B.

### ✅ Rules

| Rule | Detail |
|---|---|
| Who can request? | Student |
| Who approves? | **Both** old admin AND new admin must approve |
| Approval steps | 2 steps — Old Admin approves first, then New Admin approves |
| Data access after transfer | Old admin sees data as **READ-ONLY** (cannot edit) |
| Old booking | Marked as `completed` or `cancelled` |
| New booking | Created fresh in the new hostel |

### 🔁 Transfer Flow (Step by Step)

```
Student requests transfer to a different admin's hostel
        ↓
Old Admin reviews and APPROVES (Step 1)
        ↓
New Admin reviews and APPROVES (Step 2)
        ↓
Old booking → marked as COMPLETED/CANCELLED
New booking → created in new hostel
Student profile → updated to new hostel
Old hostel data → marked as TRANSFERRED (read-only)
        ↓
✅ Transfer Complete
```

### 📂 Data Visibility (External Transfer)

| Data Type | Old Hostel Admin | New Hostel Admin |
|---|---|---|
| Student Profile | 🔒 Read-Only (marked "Transferred") | ✅ Full Access |
| Old Payments & Invoices | 🔒 Read-Only (for accounting/audit) | ❌ Cannot see old payments |
| New Payments & Invoices | ❌ Cannot see | ✅ Full Access |
| Documents (ID, Aadhaar etc.) | 🔒 Read-Only | ✅ Full Access |
| Old Complaints | 🔒 Read-Only | ❌ Cannot see |
| New Complaints | ❌ Cannot see | ✅ Full Access |
| Attendance Records | 🔒 Read-Only (audit trail) | ✅ Full Access (from transfer date) |

> **Important:** Old hostel admin data is NEVER hard-deleted. It is marked as `[Transferred]` and becomes read-only. This is for legal, accounting, and dispute protection purposes.

---

## ❌ Transfer Rejection Rules

| Scenario | Can Transfer? | Reason |
|---|---|---|
| Student has unpaid dues | ❌ No | Must clear pending payments first |
| Student has open/pending complaint | ⚠️ Warning | Admin must resolve first |
| New hostel has no available beds | ❌ No | No room available |
| Old admin rejects | ❌ No | Transfer cancelled |
| New admin rejects | ❌ No | Transfer cancelled |

---

## 🧪 Test Cases for QA Team

### Internal Transfer (Same Admin)

| Test Case | Steps | Expected Result |
|---|---|---|
| TC-INT-01 | Student requests internal transfer | Transfer request created with status `PENDING` |
| TC-INT-02 | Admin approves internal transfer | Status changes to `COMPLETED`, student moves to new hostel |
| TC-INT-03 | Admin rejects internal transfer | Status changes to `REJECTED`, student stays in old hostel |
| TC-INT-04 | Student has unpaid dues and requests transfer | System blocks transfer with error message |
| TC-INT-05 | New hostel has no available beds | System blocks transfer with error message |
| TC-INT-06 | Verify old data visibility after transfer | Admin can see all data from both hostels with full access |
| TC-INT-07 | Verify new booking is created | After approval, a new booking exists in new hostel |
| TC-INT-08 | Verify old booking is cancelled | After approval, old booking is marked `COMPLETED`/`CANCELLED` |

---

### External Transfer (Different Admin)

| Test Case | Steps | Expected Result |
|---|---|---|
| TC-EXT-01 | Student requests external transfer | Request created with status `PENDING_OLD_ADMIN` |
| TC-EXT-02 | Old admin approves | Status changes to `PENDING_NEW_ADMIN` |
| TC-EXT-03 | New admin approves | Status changes to `COMPLETED`, student moves |
| TC-EXT-04 | Old admin rejects | Status changes to `REJECTED`, student stays in old hostel |
| TC-EXT-05 | New admin rejects | Status changes to `REJECTED`, student stays in old hostel |
| TC-EXT-06 | Verify old admin data is READ-ONLY after transfer | Old admin can SEE but CANNOT EDIT student data |
| TC-EXT-07 | Verify new admin has full access | New admin can fully edit and manage student |
| TC-EXT-08 | Verify old admin CANNOT see new payments | Old admin's panel does not show payments made after transfer |
| TC-EXT-09 | Verify new admin CANNOT see old payments | New admin's panel does not show payments made before transfer |
| TC-EXT-10 | Verify documents are accessible to new admin | New admin can see student's uploaded documents |
| TC-EXT-11 | Verify transfer is shown in audit log | System logs the transfer event with timestamp |
| TC-EXT-12 | Student has unpaid dues — blocks external transfer | System shows error, transfer not allowed |

---

## 📊 Transfer Status Flow

```
PENDING  →  (Old Admin approves)  →  PENDING_NEW_ADMIN  →  (New Admin approves)  →  COMPLETED
   ↓                                         ↓
REJECTED                                  REJECTED
(Old Admin rejects)                   (New Admin rejects)
```

For **Internal Transfer:**
```
PENDING  →  (Admin approves)  →  COMPLETED
   ↓
REJECTED
```

---

## 🔐 Security & Business Rules

> [!IMPORTANT]
> - Student data is **NEVER hard-deleted** from the old hostel. It is marked as `[Transferred]` and becomes read-only.
> - Financial records (payments, invoices) must stay with the old hostel for GST and accounting audit purposes.
> - Transfer can only happen if the student has **zero pending dues**.
> - All transfer events must be logged with timestamp, admin who approved, and date of transfer.

> [!WARNING]
> - A student cannot initiate a NEW transfer while a previous transfer is still `PENDING`.
> - Security deposit handling (refund or transfer) must be decided by the hostel admin manually — the system will NOT auto-transfer security deposits.

---

## 📝 Summary

| Feature | Internal Transfer | External Transfer |
|---|---|---|
| Approvals needed | 1 (Same Admin) | 2 (Old + New Admin) |
| Old data deleted? | ❌ Never | ❌ Never |
| Old admin access after transfer | ✅ Full Access | 🔒 Read-Only |
| New admin access after transfer | ✅ Full Access | ✅ Full Access |
| Complexity | 🟢 Simple | 🔴 Complex |



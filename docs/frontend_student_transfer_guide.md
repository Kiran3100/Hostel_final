# 🎨 Frontend Implementation Guide: Student Hostel Transfer Feature

Complete UI mockups, screen layouts, API specs, and component guide for the frontend team.

---

## 📱 Screen 1 — Student App: Active Transfer & Progress Stepper

![Student App Active Transfer](images/student_transfer_request_ui.png)

### What to Build:
- **Route:** `/student/transfers`
- **Active Banner Card** — show if student has a pending transfer:
  - From Hostel → To Hostel (with arrow)
  - Current status badge (color-coded)
  - Progress Stepper (see state machine below)
  - "Cancel Request" button (only when status is `pending` / `pending_old_admin` / `pending_new_admin`)
- **Transfer History List** — past transfers (completed / rejected / cancelled)
- **CTA Button** — "Request New Transfer" (disabled if active transfer exists)

### Status Badge Colors:
| Status | Badge Color |
|---|---|
| `pending` | 🟡 Yellow |
| `pending_old_admin` | 🟠 Orange |
| `pending_new_admin` | 🔵 Blue |
| `completed` | 🟢 Green |
| `rejected` | 🔴 Red |
| `cancelled` | ⚫ Gray |

---

## 📱 Screen 2 — Student App: New Transfer Request Form

![Student App Transfer Request Form Modal](images/student_transfer_form_ui.png)

### What to Build:
- **Route / Modal:** `/student/transfers/new`
- **Form Fields:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `to_hostel_id` | Dropdown | ✅ Yes | Fetch all hostels, exclude current hostel |
| `to_room_id` | Dropdown | ❌ No | Load after hostel selected |
| `to_bed_id` | Dropdown | ❌ No | Load after room selected, filter AVAILABLE only |
| `reason` | Textarea | ❌ No | Free text, 500 chars max |

- **Warning Box** — amber alert shown when response `warning` field is not null:
  ```
  ⚠️ You have open/pending complaints.
  Admin is advised to resolve them before approving.
  ```
- **Submit Button** → calls `POST /api/v1/student/transfers`

---

## 💻 Screen 3 — Admin Dashboard: Transfer Requests Table + Approval Modal

![Admin Dashboard Transfer Management](images/admin_transfer_dashboard_ui.png)

### What to Build:
- **Route:** `/admin/hostels/:hostelId/transfers`
- **New Tab** in Hostel Management section: label = **"Transfers"**
- **Transfers Table Columns:**
  - Student Name + Photo
  - Transfer Type: `INTERNAL` badge (Blue) / `EXTERNAL` badge (Purple)
  - Direction: `Hostel A → Hostel B`
  - Status (color-coded badge)
  - Requested Date
  - Actions: **[Approve]** / **[Reject]** buttons (hidden for completed/rejected)

### Approve Modal Logic (Dynamic):

**Case A — Outgoing Step 1 (Old Admin, External Transfer):**
- Status is `pending_old_admin` AND `from_hostel_id` matches current admin's hostel
- Show: *"Approving will forward to the target hostel admin for bed assignment."*
- No room/bed selector needed
- API payload: `{ "action": "approve", "note": "..." }`

**Case B — Incoming Final Step OR Internal Transfer:**
- Status is `pending_new_admin` (incoming) OR `pending` (internal)
- Show: Room dropdown + Bed dropdown (load AVAILABLE beds only)
- Both `to_room_id` and `to_bed_id` are **REQUIRED**
- API payload: `{ "action": "approve", "to_room_id": "...", "to_bed_id": "...", "note": "..." }`

### Reject Modal:
- Simple confirmation modal with optional note
- API payload: `{ "action": "reject", "note": "..." }`

---

## 💻 Screen 4 — Admin Dashboard: Transferred-Out Students (Read-Only)

![Admin Dashboard Transferred Out Students Read-Only](images/admin_transferred_students_ui.png)

### What to Build:
- **Route:** `/admin/hostels/:hostelId/transferred-students`
- **New Tab** in Hostel Management section: label = **"Transferred Out"**
- **Top Banner:** 🔒 *"Historical Read-Only View — Data preserved for legal and audit purposes."*
- **Table Columns:**
  - Student Name & Student Number
  - Email / Phone
  - Moved To: Target Hostel Name
  - Transfer Completed Date
  - Original Check-In Date
  - Status Badge: `TRANSFERRED - READ ONLY` (gray, locked icon)
- **All edit/delete buttons disabled** for records returned from this endpoint
- `access_level === "READ_ONLY"` → disable all mutation UI elements

---

## 🌐 API Integration Reference

### Base URL: `https://hostel-final.onrender.com`

### Student Endpoints:

#### POST `/api/v1/student/transfers` — Request Transfer
```json
// Request
{
  "to_hostel_id": "uuid",
  "to_room_id": "uuid-optional",
  "to_bed_id": "uuid-optional",
  "reason": "Closer to campus"
}

// Response 201
{
  "id": "trans-uuid",
  "transfer_type": "external",
  "status": "pending_old_admin",
  "from_hostel_name": "Nestora Alpha",
  "to_hostel_name": "Nestora Beta",
  "warning": "⚠️ You have open/pending complaints...",
  "created_at": "2026-07-30T12:00:00Z"
}
```

#### GET `/api/v1/student/transfers` — Transfer History
Returns array of transfer objects.

#### POST `/api/v1/student/transfers/{id}/cancel` — Cancel Transfer
No body needed.

---

### Admin Endpoints:

#### GET `/api/v1/admin/hostels/{hostel_id}/transfers` — List Transfer Requests
Returns all incoming + outgoing transfers for the hostel.

#### POST `/api/v1/admin/transfers/{id}/action` — Approve or Reject
```json
// Approve (Final step)
{
  "action": "approve",
  "to_room_id": "room-uuid",
  "to_bed_id": "bed-uuid",
  "note": "Bed assigned in Room 101"
}

// Approve (Step 1 forward only)
{
  "action": "approve",
  "note": "Forwarded to target admin"
}

// Reject
{
  "action": "reject",
  "note": "No suitable beds available"
}
```

#### GET `/api/v1/admin/hostels/{hostel_id}/transferred-students` — Read-Only Historical Students
```json
// Response
[
  {
    "student_id": "uuid",
    "student_number": "STU-2026-004",
    "full_name": "Rahul Sharma",
    "email": "rahul@example.com",
    "phone": "9876543210",
    "transferred_to_hostel": "Nestora Beta",
    "transfer_completed_at": "2026-07-30T12:30:00Z",
    "original_check_in_date": "2026-01-01",
    "access_level": "READ_ONLY",
    "status_label": "TRANSFERRED"
  }
]
```

---

## 🔄 Stepper State Machine

```
INTERNAL TRANSFER:
  ┌──────────┐    Admin Approves    ┌───────────┐
  │ PENDING  │ ──────────────────► │ COMPLETED │
  └──────────┘                     └───────────┘
       │ Admin Rejects
       ▼
  ┌──────────┐
  │ REJECTED │
  └──────────┘

EXTERNAL TRANSFER:
  ┌──────────────────┐   Old Admin   ┌──────────────────┐   New Admin   ┌───────────┐
  │ PENDING_OLD_ADMIN│ ────────────► │ PENDING_NEW_ADMIN│ ────────────► │ COMPLETED │
  └──────────────────┘   Approves    └──────────────────┘   Approves    └───────────┘
           │                                  │
           │ Either Admin Rejects             │
           ▼                                  ▼
      ┌──────────┐                      ┌──────────┐
      │ REJECTED │                      │ REJECTED │
      └──────────┘                      └──────────┘
```

---

## ⚠️ Error Handling Reference

| HTTP Code | Scenario | UI Response |
|---|---|---|
| `400 Bad Request` | Unpaid dues | 🔴 Banner: *"Clear pending dues before requesting transfer."* |
| `409 Conflict` | No available beds | 🟡 Toast: *"Target hostel has no available beds."* |
| `409 Conflict` | Active transfer exists | Disable "New Transfer" button, show notice |
| `403 Forbidden` | Edit on transferred student | 🔒 Alert: *"This record is read-only — student has transferred out."* |
| `404 Not Found` | Invalid transfer ID | Redirect to transfers list |

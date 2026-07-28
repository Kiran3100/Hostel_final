# Frontend Task — Razorpay Route Settings
### What to change, where to change, and what the new UI looks like

> **Existing Page:** `/admin/payment-settings`  
> **Existing Spec:** `frontend_payment_settings_spec.md`  
> **Task:** Add Razorpay Route (Split Payment) support to the EXISTING payment settings page  
> **Do NOT create a new page — only modify the existing one**

---

## 🎯 Simple Summary for the Team

The existing payment settings page has **one mode** (Direct Keys).  
You need to add **a second mode** (Razorpay Route).  
Nothing else changes anywhere in the frontend.

```
BEFORE (existing page):
  [ Key ID field      ]
  [ Key Secret field  ]
  [ Save button       ]

AFTER (updated page):
  ● Direct Integration   ○ Razorpay Route
  
  IF "Direct" selected:     IF "Route" selected:
  [ Key ID field      ]     [ Linked Account ID ]
  [ Key Secret field  ]     [ Platform Fee %    ]
  [ Save button       ]     [ Save button       ]
```

---

## 📍 Exact Location — Where to Edit

This is the ONLY file/component you need to touch:

| What | Where |
|---|---|
| Page route | `/admin/payment-settings` |
| Existing spec to refer to | `frontend_payment_settings_spec.md` |
| Components to modify | `PaymentStatusCard` + `PaymentConfigForm` (already defined in spec) |
| New component to add | `PaymentModeToggle` (described below) |

---

## 🔧 Step-by-Step Changes

---

### CHANGE 1 — Add a Mode Toggle at the top of the form

**Where:** Inside the existing `PaymentConfigForm` component, add this ABOVE the Key ID field.

```jsx
// NEW — Add this above your existing Key ID input
const [mode, setMode] = useState("direct"); // "direct" or "route"

<div className="payment-mode-toggle">
  <label>Payment Mode</label>
  <div className="toggle-group">
    <button
      className={mode === "direct" ? "active" : ""}
      onClick={() => setMode("direct")}
    >
      💳 Direct Integration
    </button>
    <button
      className={mode === "route" ? "active" : ""}
      onClick={() => setMode("route")}
    >
      ⚡ Razorpay Route (Split Payment)
    </button>
  </div>
</div>
```

---

### CHANGE 2 — Show different form fields based on selected mode

**Where:** Replace the existing form fields section with a conditional render.

```jsx
{/* EXISTING fields — show only when mode === "direct" */}
{mode === "direct" && (
  <>
    <input
      label="Razorpay Key ID"
      placeholder="rzp_live_xxxxxxxxxx"
      value={form.razorpay_key_id}
      onChange={...}
    />
    <PasswordToggleInput
      label="Razorpay Key Secret"
      value={form.razorpay_key_secret}
      onChange={...}
    />
    <PasswordToggleInput
      label="Webhook Secret (optional)"
      value={form.razorpay_webhook_secret}
      onChange={...}
    />
  </>
)}

{/* NEW fields — show only when mode === "route" */}
{mode === "route" && (
  <>
    <input
      label="Razorpay Linked Account ID"
      placeholder="acc_XXXXXXXXXX"
      helperText="Get this from your Razorpay dashboard after hostel admin completes KYC"
      value={form.razorpay_linked_account_id}
      onChange={...}
    />
    <input
      type="number"
      label="Platform Fee %"
      placeholder="5"
      min={0}
      max={100}
      helperText="You keep this % from every student payment. Hostel gets the rest."
      value={form.platform_fee_percentage}
      onChange={...}
    />
  </>
)}
```

---

### CHANGE 3 — Update the API call on Save

**Where:** In the form's `handleSubmit` function.

```javascript
// EXISTING save function — UPDATE this
const handleSubmit = async () => {
  let body = { is_active: form.is_active };

  if (mode === "direct") {
    // EXISTING logic — no change
    body.razorpay_key_id = form.razorpay_key_id;
    if (form.razorpay_key_secret) body.razorpay_key_secret = form.razorpay_key_secret;
    if (form.razorpay_webhook_secret) body.razorpay_webhook_secret = form.razorpay_webhook_secret;
  }

  if (mode === "route") {
    // NEW logic
    body.razorpay_linked_account_id = form.razorpay_linked_account_id;
    body.platform_fee_percentage = parseFloat(form.platform_fee_percentage);
  }

  // API call — same endpoint as before, just different body
  await api.patch(`/admin/hostels/${hostelId}/payment-config`, body);
};
```

---

### CHANGE 4 — Update the Status Card to show payment mode

**Where:** In your existing `PaymentStatusCard` component — add a mode badge.

```jsx
// EXISTING status card — add this badge line
<PaymentStatusCard>
  {config.is_configured && (
    <>
      <StatusBadge status={config.is_active ? "active" : "inactive"} />
      
      {/* NEW — add this badge */}
      {config.payment_mode === "route" && (
        <Badge color="green">⚡ Split Payments Active</Badge>
      )}
      {config.payment_mode === "direct" && (
        <Badge color="blue">💳 Direct Integration</Badge>
      )}
      
      {/* Show relevant info based on mode */}
      {config.payment_mode === "direct" && (
        <p>Key ID: {maskKeyId(config.razorpay_key_id)}</p>
      )}
      {config.payment_mode === "route" && (
        <p>Linked Account: {config.razorpay_linked_account_id}</p>
        <p>Platform Fee: {config.platform_fee_percentage}%</p>
      )}
    </>
  )}
</PaymentStatusCard>
```

---

### CHANGE 5 — Pre-fill the mode on page load

**Where:** In your existing `useEffect` that loads the config from the API.

```javascript
// EXISTING useEffect — add mode detection
useEffect(() => {
  const fetchConfig = async () => {
    const data = await api.get(`/admin/hostels/${hostelId}/payment-config`);
    setConfig(data);

    // NEW — detect and pre-select the mode
    if (data.payment_mode === "route") {
      setMode("route");
      setForm({
        razorpay_linked_account_id: data.razorpay_linked_account_id || "",
        platform_fee_percentage: data.platform_fee_percentage || 0,
        is_active: data.is_active,
      });
    } else {
      setMode("direct");
      setForm({
        razorpay_key_id: data.razorpay_key_id || "",
        razorpay_key_secret: "",      // never prefill secret
        razorpay_webhook_secret: "",  // never prefill secret
        is_active: data.is_active,
      });
    }
  };
  fetchConfig();
}, [hostelId]);
```

---

## ✅ Frontend Validation Rules (new fields)

| Field | Rule |
|---|---|
| `razorpay_linked_account_id` | Required in Route mode. Must start with `acc_` |
| `platform_fee_percentage` | Required in Route mode. Number between `0` and `100` |

```javascript
// Add this to your existing validation function
if (mode === "route") {
  if (!form.razorpay_linked_account_id.startsWith("acc_")) {
    setError("Linked Account ID must start with acc_");
    return;
  }
  if (form.platform_fee_percentage < 0 || form.platform_fee_percentage > 100) {
    setError("Platform fee must be between 0 and 100");
    return;
  }
}
```

---

## 📡 Updated API Response — New Fields

The existing `GET /api/v1/admin/payment-config` response now has 3 new fields:

```json
{
  "hostel_id": "uuid",
  "razorpay_key_id": "rzp_live_xxx",
  "is_active": true,
  "is_configured": true,

  // 👇 NEW fields — use these
  "payment_mode": "route",
  "razorpay_linked_account_id": "acc_XXXXXXXXXX",
  "platform_fee_percentage": 5.0
}
```

> `payment_mode` will be `"direct"`, `"route"`, or `"unconfigured"`

---

## 🙅 What you do NOT need to touch

| Area | Reason |
|---|---|
| Student checkout page | Backend handles split automatically |
| Razorpay modal code | No change — same `key_id` + `order_id` flow |
| Payment verification | No change |
| Billing/invoice pages | No change |
| Any other admin pages | No change |

---

## 🧪 Testing Checklist

- [ ] Page loads and shows correct mode badge (Direct / Route)
- [ ] Clicking "Razorpay Route" tab hides Key ID fields, shows acc_ + fee% fields
- [ ] Clicking "Direct Integration" tab shows Key ID fields, hides acc_ fields
- [ ] Saving with `acc_` ID calls PATCH with correct body
- [ ] Saving with invalid `acc_` prefix shows validation error
- [ ] Status card shows correct badge after save
- [ ] Page refreshes and pre-selects the correct mode tab

---

## 📞 API Base URL

```
Production: https://hostel-final-cqes.onrender.com
Swagger Docs: https://hostel-final-cqes.onrender.com/docs
```

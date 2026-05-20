# Admin Handbook - BEFS

## 1. Introduction
This handbook is the definitive guide for administrators of the BEFS system ("KI Kollega"). It covers system monitoring, security, data governance, and user management.

## 2. Accessibility & System Tools
### 2.1 The Dashboard
The main entry point for monitoring the system is the **Dashboard** (`/dashboard`). It provides real-time metrics on:
*   Active properties and contracts
*   System health (Database, API connectivity)
*   Cost monitoring (External API usage)

## 3. Data Governance & Security
BEFS handles sensitive financial and personal data. Strict governance policies are enforced.

### 3.1 Data Classification
All data in the system is classified into three levels:
*   **Public/Internal:** Addresses, general building info. (Low risk)
*   **Internal:** Operational logs, maintenance records. (Medium risk)
*   **Restricted:** Financials (rent, expenses), PII (Personal Identifiable Information). (High risk - REQUIRES AUDIT)

### 3.2 Governance Dashboard (`/admin/governance`)
This tool provides a real-time audit of the database schema:
*   **Sensitivity Scan:** Identifies tables containing "Restricted" data.
*   **JSON Inspection:** Flags un-typed JSON fields (`external_data`, `amount`) that may contain hidden financial data.
*   **Metrics:** Shows the distribution of sensitive vs. non-sensitive fields.

**Usage:**
1.  Navigate to **Admin -> Governance**.
2.  Review the **"Top Sensitive Areas"** card to prioritize security audits.
3.  Check the **"Unstructured JSON"** metric. A high number indicates data sprawl that should be standardized.
4.  Use the **Edit** icon in the **Full Data Catalog** table to add or update descriptions for data fields. This helps document data usage and sensitivity.

### 3.3 GDPR & Privacy
*   **Right to Erasure:** Use the `Delete User` function in User Management to anonymize personal data.
*   **Access Logs:** All access to restricted data is logged in `audit_logs`.

## 4. User Management (`/admin/users`)
*   **Roles:**
    *   `Superuser`: Full system access including governance tools.
    *   `Admin`: Managing properties and users.
    *   `User`: Standard access to properties.
*   **Onboarding:** New admins must be approved by an existing Superuser.

## 5. Troubleshooting
*   **Database connection:** Check `/health` endpoint.
*   **API Errors:** Review logs in `api_call_logs`.

## 6. Functional Admin Tools
Beyond user management and governance, admins have access to powerful tools for daily operations and strategic planning.

### 6.1 Role Simulation (`/admin/simulation`)
Admins can verify what different users see by simulating their roles.
*   **Usage:** Click the "Bytt rolle" button in the header.
*   **Purpose:** Debug permissions, verify view access for specific roles (e.g., "Vaktmester" seeing only maintenance tasks).
*   **Note:** While simulating, the admin sidebar is hidden. To exit, click "Simulering" -> "Ingen (Admin)".

### 6.2 Financial Insight (`/admin/financial-insight`)
A dedicated search engine for the finance team.
*   **Features:**
    *   Search across all properties by name/address.
    *   Aggregated view of Costs vs. Revenue.
    *   Vendor analysis: Specific breakdown of payments to suppliers.
    *   Status flags: Identifies properties with missing budget or accounting data.

### 6.3 External Risk Assessment (`/admin/risk`)
Batch processing tool for updating environmental risk data.
*   **NVE Flood & Landslide:** Automatically queries NVE APIs for all property coordinates.
*   **Result:** Updates the risk score and tags properties with "Flomfare" or "Skredfare" in the Risk Picture.

### 6.4 Risk Picture (Prioritization)
The system calculates a "Prioritization Index" to help allocate maintenance funds.
*   **Formula:** `Risk Score` × `Annual Cost`.
*   **Goal:** High cost properties with high risk/deviations get top priority.
*   **Access:** Available via the "Risikobildet" link in the admin dashboard.

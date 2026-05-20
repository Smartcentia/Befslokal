# ERP Ingestion Specification (v1.0)
**Status**: REQUIRED TO UNBLOCK PHASE 4

To implement the `FUNDS` (DIM1 ↔ BIRK) and `BOOKED_ON` (DIM1 ↔ PROPERTY) relations, we require an export from Agresso/Unit4 with the following structure.

## 1. Required Columns

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `Dim1` | String | The Accounting Unit/Department code. | `414101` |
| `Dim1(T)` | String | The display name/text for Dim1. | `V-1-RN-RØU` |
| `Account` | String | GL Account number (for Rent Variance logic). | `6000` |
| `Account(T)` | String | GL Account description. | `Husleie` |
| `Period` | String | FY and accounting period. | `202401` |
| `Amount` | Decimal | The booked transaction amount. | `54200.50` |
| `VoucherType` | String | (Optional) To filter actuals from budgets. | `GL` |

## 2. File Format
- **Format**: CSV, UTF-8 encoded.
- **Delimiter**: Semicolon (`;`) or Comma (`,`).
- **Path**: Place in `/data/in/erp_raw.csv`.

## 3. Ingestion Logic (Phase 4)
1. **FUNDS Mapping**: Link `Dim1` to `BIRK.EnhetID` (Exact match).
2. **BOOKED_ON Mapping**: Heuristic match between `Dim1(T)` and `PROPERTY.Adresse`.
3. **KPI Calculation**:
   - `Rent_Variance = SUM(Amount where Account in RENT_GROUP) - Contract_Value`.

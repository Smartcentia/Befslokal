-- Verifisering: eiendomsside (verify-db / verify-gl / verify-budget)
-- FVK Lofoten / Stokmarknes — kjør mot prod med pooler- eller direkte-URL:
--   railway run -- psql "$DATABASE_URL" …
-- (konverter postgresql+asyncpg:// til postgresql:// for psql)
--
-- Produksjon (Railway/BEF EIENDOM): «FVK, Lofoten og Vesterålen», Markedsgt 20 — den som matcher skjermbilder
-- (Nordnesveien 3 er en annen rad med samme navn). Bytt UUID for andre eiendommer.

-- === verify-db: properties + center ===
SELECT
  p.property_id,
  p.name,
  p.address,
  p.city,
  p.postal_code,
  p.latitude,
  p.longitude,
  p.department_code,
  p.department_name,
  p.koststed_kode,
  p.construction_year,
  p.approved_places,
  p.budgeted_places,
  p.center_id,
  c.name AS center_name,
  p.ownership_type,
  p.unit_id_erp,
  p.unit_short_type,
  p.unit_type_derived,
  p.owner_name
FROM properties p
LEFT JOIN centers c ON c.center_id = p.center_id
WHERE p.property_id = 'f9cdf6ff-74e6-45c7-b382-aecd5dea68cd'::uuid;

-- === verify-gl: gl_transactions 2026 for property_id ===
SELECT
  COUNT(*) AS antall_poster,
  COALESCE(SUM(belop), 0) AS sum_belop
FROM gl_transactions
WHERE property_id = 'f9cdf6ff-74e6-45c7-b382-aecd5dea68cd'::uuid
  AND ar = 2026;

-- === verify-gl: dim1 (koststed) ===
SELECT g.dim1_kode,
       COUNT(*) AS antall_poster,
       COALESCE(SUM(g.belop), 0) AS sum_belop
FROM gl_transactions g
WHERE g.ar = 2026
  AND g.dim1_kode IN (
    SELECT department_code FROM properties WHERE property_id = 'f9cdf6ff-74e6-45c7-b382-aecd5dea68cd'::uuid AND department_code IS NOT NULL
    UNION
    SELECT koststed_kode FROM properties WHERE property_id = 'f9cdf6ff-74e6-45c7-b382-aecd5dea68cd'::uuid AND koststed_kode IS NOT NULL
  )
GROUP BY g.dim1_kode;

-- === verify-budget: budget 2026 ===
SELECT
  COUNT(*) AS antall_rader,
  COALESCE(SUM(amount), 0) AS sum_amount
FROM budget
WHERE property_id = 'f9cdf6ff-74e6-45c7-b382-aecd5dea68cd'::uuid
  AND year = 2026;

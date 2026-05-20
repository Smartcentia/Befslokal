
-- Ghost Property Remediation Script (v2)
-- Generated based on Offline Analysis (System CSV vs Master CSV)
-- Action: DELETE confirmed test data, RENAME poorly named real properties, ENRICH missing data.

BEGIN;

---------------------------------------------------------------------------
-- 1. DELETE TEST DATA
---------------------------------------------------------------------------
-- "Wenchebo" is confirmed test data (not in Master, address "Ukjent")
DELETE FROM properties 
WHERE name ILIKE 'Wenchebo%';

-- Any other obvious test patterns
DELETE FROM properties 
WHERE name ILIKE 'Test Property%' OR name ILIKE 'Demo Eiendom%';

---------------------------------------------------------------------------
-- 2. RENAME POORLY NAMED REAL PROPERTIES
---------------------------------------------------------------------------
-- "Ny Signert Lunde" -> "Lunde" (Lundeveien 171)
UPDATE properties SET name = 'Lunde', updated_at = NOW() 
WHERE name ILIKE 'Ny Signert Lunde%';

-- "Ny Signert Katfoss" -> "Katfoss" (Ilaugveien 1)
UPDATE properties SET name = 'Katfoss', updated_at = NOW() 
WHERE name ILIKE 'Ny Signert Katfoss%';

-- "Ny i finansliste... Lokketomarka" -> "Morvik"
UPDATE properties SET name = 'Morvik', updated_at = NOW() 
WHERE address ILIKE '%Lokketomarka 24%';

-- "Ny Kantum.pdf" -> "Kantum"
UPDATE properties SET name = 'Kantum', updated_at = NOW() 
WHERE name ILIKE 'Ny Kantum%';

---------------------------------------------------------------------------
-- 3. ENRICH MISSING DATA (Real Properties)
---------------------------------------------------------------------------

-- Eikelund (Master: Sandbrekkevegen 27, 3647 m2)
UPDATE properties 
SET total_area = 3647, address = 'Sandbrekkevegen 27', updated_at = NOW()
WHERE name ILIKE '%Eikelund%' AND (total_area IS NULL OR total_area < 1);

-- Solbakken (Master: 1398 m2)
UPDATE properties 
SET total_area = 1398, updated_at = NOW()
WHERE name ILIKE 'Solbakken%' AND (total_area IS NULL OR total_area < 1);

-- Vikhovlia 1400 (Master: 1280 m2)
UPDATE properties 
SET total_area = 1280, updated_at = NOW()
WHERE address ILIKE '%Vikhovlia%' AND (total_area IS NULL OR total_area < 1);

-- Peder Myhres vei 16 (Master: 1000 m2)
UPDATE properties 
SET total_area = 1000, updated_at = NOW()
WHERE address ILIKE '%Peder Myhres%' AND (total_area IS NULL OR total_area < 1);

-- Fridtjof Nansens vei (Master: 695 m2 - Likely Furuly)
UPDATE properties 
SET total_area = 695, updated_at = NOW()
WHERE address ILIKE '%Fridtjof Nansens%' AND (total_area IS NULL OR total_area < 1);

-- Skjerven (Master: 1667 m2)
UPDATE properties 
SET total_area = 1667, updated_at = NOW()
WHERE name ILIKE 'Skjerven%' AND (total_area IS NULL OR total_area < 1);

-- Borg (Likely Storveien 121 - 569 m2)
UPDATE properties 
SET total_area = 569, updated_at = NOW()
WHERE name ILIKE 'Borg%' AND (total_area IS NULL OR total_area < 1);

COMMIT;

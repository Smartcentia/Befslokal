-- Critical indexes for performance optimization
-- Based on user request

CREATE INDEX IF NOT EXISTS idx_parties_name ON parties(name);
CREATE INDEX IF NOT EXISTS idx_parties_orgnr ON parties(orgnr);

CREATE INDEX IF NOT EXISTS idx_properties_address ON properties(address);
CREATE INDEX IF NOT EXISTS idx_properties_city ON properties(city);
CREATE INDEX IF NOT EXISTS idx_properties_name ON properties(name);
CREATE INDEX IF NOT EXISTS idx_properties_region ON properties(region);
-- Full text search index
CREATE INDEX IF NOT EXISTS idx_properties_fulltext ON properties USING GIN (to_tsvector('norwegian', name || ' ' || address || ' ' || city || ' ' || region));

CREATE INDEX IF NOT EXISTS idx_units_property_id ON units(property_id);

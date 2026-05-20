"""Add risk assessment tables

Revision ID: 003_add_risk_assessment_tables
Revises: 002_add_import_tables
Create Date: 2024-11-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '003_add_risk_assessment_tables'
down_revision = '002_add_import_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if properties.property_id exists - used for all FK references below
    op.execute(text("""
        DO $$
        DECLARE
            has_property_id BOOLEAN;
        BEGIN
            -- Check if property_id column exists in properties table
            has_property_id := EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'properties'
                    AND column_name = 'property_id'
            );

            -- Create risk_assessments table (conditionally with/without FK)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'risk_assessments'
            ) THEN
                IF has_property_id THEN
                    CREATE TABLE risk_assessments (
                        assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
                        assessment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        methodology VARCHAR(50) NOT NULL,
                        overall_risk_score FLOAT NOT NULL CHECK (overall_risk_score >= 0 AND overall_risk_score <= 100),
                        risk_category VARCHAR(20) NOT NULL CHECK (risk_category IN ('low', 'medium', 'high', 'critical')),
                        assessed_by VARCHAR(255),
                        notes TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                ELSE
                    -- Create without FK if property_id doesn't exist
                    CREATE TABLE risk_assessments (
                        assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL,
                        assessment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        methodology VARCHAR(50) NOT NULL,
                        overall_risk_score FLOAT NOT NULL CHECK (overall_risk_score >= 0 AND overall_risk_score <= 100),
                        risk_category VARCHAR(20) NOT NULL CHECK (risk_category IN ('low', 'medium', 'high', 'critical')),
                        assessed_by VARCHAR(255),
                        notes TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                END IF;
            END IF;

            -- Create risk_factors table (always with FK to risk_assessments since it's created above)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'risk_factors'
            ) AND EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'risk_assessments'
            ) THEN
                CREATE TABLE risk_factors (
                    factor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    assessment_id UUID NOT NULL REFERENCES risk_assessments(assessment_id) ON DELETE CASCADE,
                    category VARCHAR(50) NOT NULL,
                    factor_name VARCHAR(100) NOT NULL,
                    severity FLOAT NOT NULL CHECK (severity >= 0 AND severity <= 10),
                    probability FLOAT NOT NULL CHECK (probability >= 0 AND probability <= 1),
                    weight FLOAT NOT NULL CHECK (weight >= 0 AND weight <= 1),
                    data_source VARCHAR(100),
                    raw_data JSONB,
                    calculated_score FLOAT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            END IF;

            -- Create proximity_services table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'proximity_services'
            ) THEN
                IF has_property_id THEN
                    CREATE TABLE proximity_services (
                        service_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
                        service_type VARCHAR(50) NOT NULL,
                        service_name VARCHAR(255),
                        distance_meters FLOAT,
                        travel_time_minutes FLOAT,
                        latitude FLOAT,
                        longitude FLOAT,
                        rating FLOAT,
                        address VARCHAR(500),
                        phone VARCHAR(50),
                        data_source VARCHAR(50),
                        fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE
                    );
                ELSE
                    CREATE TABLE proximity_services (
                        service_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL,
                        service_type VARCHAR(50) NOT NULL,
                        service_name VARCHAR(255),
                        distance_meters FLOAT,
                        travel_time_minutes FLOAT,
                        latitude FLOAT,
                        longitude FLOAT,
                        rating FLOAT,
                        address VARCHAR(500),
                        phone VARCHAR(50),
                        data_source VARCHAR(50),
                        fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE
                    );
                END IF;
            END IF;

            -- Create geological_data table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'geological_data'
            ) THEN
                IF has_property_id THEN
                    CREATE TABLE geological_data (
                        geo_data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
                        bedrock_type VARCHAR(100),
                        soil_type VARCHAR(100),
                        groundwater_depth FLOAT,
                        landslide_risk VARCHAR(20) CHECK (landslide_risk IN ('low', 'medium', 'high', 'critical')),
                        quickclay_risk BOOLEAN,
                        seismic_zone INTEGER,
                        data_source VARCHAR(50),
                        raw_data JSONB,
                        fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE
                    );
                ELSE
                    CREATE TABLE geological_data (
                        geo_data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL,
                        bedrock_type VARCHAR(100),
                        soil_type VARCHAR(100),
                        groundwater_depth FLOAT,
                        landslide_risk VARCHAR(20) CHECK (landslide_risk IN ('low', 'medium', 'high', 'critical')),
                        quickclay_risk BOOLEAN,
                        seismic_zone INTEGER,
                        data_source VARCHAR(50),
                        raw_data JSONB,
                        fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE
                    );
                END IF;
            END IF;

            -- Create environmental_data table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'environmental_data'
            ) THEN
                IF has_property_id THEN
                    CREATE TABLE environmental_data (
                        env_data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
                        air_quality_index FLOAT,
                        noise_level_db FLOAT,
                        pollution_sources JSONB,
                        contaminated_sites_nearby JSONB,
                        data_source VARCHAR(50),
                        fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE
                    );
                ELSE
                    CREATE TABLE environmental_data (
                        env_data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL,
                        air_quality_index FLOAT,
                        noise_level_db FLOAT,
                        pollution_sources JSONB,
                        contaminated_sites_nearby JSONB,
                        data_source VARCHAR(50),
                        fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE
                    );
                END IF;
            END IF;

            -- Create socioeconomic_data table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'socioeconomic_data'
            ) THEN
                IF has_property_id THEN
                    CREATE TABLE socioeconomic_data (
                        socio_data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
                        municipality_code VARCHAR(10),
                        crime_rate_per_1000 FLOAT,
                        unemployment_rate FLOAT,
                        median_income DECIMAL(15, 2),
                        population_density FLOAT,
                        demographic_profile JSONB,
                        data_source VARCHAR(50),
                        year INTEGER,
                        fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE
                    );
                ELSE
                    CREATE TABLE socioeconomic_data (
                        socio_data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL,
                        municipality_code VARCHAR(10),
                        crime_rate_per_1000 FLOAT,
                        unemployment_rate FLOAT,
                        median_income DECIMAL(15, 2),
                        population_density FLOAT,
                        demographic_profile JSONB,
                        data_source VARCHAR(50),
                        year INTEGER,
                        fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE
                    );
                END IF;
            END IF;

            -- Create natural_hazard_events table (no FK dependencies)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'natural_hazard_events'
            ) THEN
                CREATE TABLE natural_hazard_events (
                    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    latitude FLOAT NOT NULL,
                    longitude FLOAT NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    event_date DATE,
                    severity VARCHAR(20) CHECK (severity IN ('minor', 'moderate', 'severe', 'catastrophic')),
                    description TEXT,
                    casualties INTEGER,
                    property_damage DECIMAL(15, 2),
                    radius_affected_meters FLOAT,
                    data_source VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            END IF;
        END
        $$;
    """))

    # Create indexes separately (only if tables exist)
    op.execute(text("""
        DO $$
        BEGIN
            -- Indexes for risk_assessments
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'risk_assessments') THEN
                CREATE INDEX IF NOT EXISTS ix_risk_assessments_property_id ON risk_assessments(property_id);
                CREATE INDEX IF NOT EXISTS ix_risk_assessments_assessment_date ON risk_assessments(assessment_date);
                CREATE INDEX IF NOT EXISTS ix_risk_assessments_risk_category ON risk_assessments(risk_category);
            END IF;

            -- Indexes for risk_factors
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'risk_factors') THEN
                CREATE INDEX IF NOT EXISTS ix_risk_factors_assessment_id ON risk_factors(assessment_id);
                CREATE INDEX IF NOT EXISTS ix_risk_factors_category ON risk_factors(category);
                CREATE INDEX IF NOT EXISTS ix_risk_factors_factor_name ON risk_factors(factor_name);
            END IF;

            -- Indexes for proximity_services
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'proximity_services') THEN
                CREATE INDEX IF NOT EXISTS ix_proximity_services_property_id ON proximity_services(property_id);
                CREATE INDEX IF NOT EXISTS ix_proximity_services_service_type ON proximity_services(service_type);
                CREATE INDEX IF NOT EXISTS ix_proximity_services_distance ON proximity_services(distance_meters);
            END IF;

            -- Indexes for geological_data
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'geological_data') THEN
                CREATE INDEX IF NOT EXISTS ix_geological_data_property_id ON geological_data(property_id);
                CREATE INDEX IF NOT EXISTS ix_geological_data_landslide_risk ON geological_data(landslide_risk);
            END IF;

            -- Indexes for environmental_data
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'environmental_data') THEN
                CREATE INDEX IF NOT EXISTS ix_environmental_data_property_id ON environmental_data(property_id);
            END IF;

            -- Indexes for socioeconomic_data
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'socioeconomic_data') THEN
                CREATE INDEX IF NOT EXISTS ix_socioeconomic_data_property_id ON socioeconomic_data(property_id);
                CREATE INDEX IF NOT EXISTS ix_socioeconomic_data_municipality ON socioeconomic_data(municipality_code);
                CREATE INDEX IF NOT EXISTS ix_socioeconomic_data_year ON socioeconomic_data(year);
            END IF;

            -- Indexes for natural_hazard_events
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'natural_hazard_events') THEN
                CREATE INDEX IF NOT EXISTS ix_natural_hazard_events_location ON natural_hazard_events(latitude, longitude);
                CREATE INDEX IF NOT EXISTS ix_natural_hazard_events_type ON natural_hazard_events(event_type);
                CREATE INDEX IF NOT EXISTS ix_natural_hazard_events_date ON natural_hazard_events(event_date);
                CREATE INDEX IF NOT EXISTS ix_natural_hazard_events_severity ON natural_hazard_events(severity);
            END IF;
        END
        $$;
    """))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS socioeconomic_data CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS environmental_data CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS natural_hazard_events CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS geological_data CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS proximity_services CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS risk_factors CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS risk_assessments CASCADE"))

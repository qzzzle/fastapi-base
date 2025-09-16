-- EI Tracker Database Schema
-- Version: 1.1.2
-- Timezone: Asia/Tehran (UTC+03:30)

-- =============================================
-- ENUMS AND TYPES
-- =============================================

-- Band type enumeration
CREATE TYPE band_type_enum AS ENUM ('ULBand', 'DLBand');

-- MVO status enumeration
CREATE TYPE mvo_status_enum AS ENUM (
    'Open, Under Investigation by CRA',
    'Solved by CRA',
    'Resolved automatically',
    'Open, Confirmed by CRA',
    'Open, Mismatch'
);

-- Technology enumeration (extensible)
CREATE TYPE technology_enum AS ENUM ('GSM', 'UMTS', 'LTE', 'NR');

-- Band enumeration
CREATE TYPE band_enum AS ENUM ('900', '1800', '2100', '2300', '2600', '3500');

-- =============================================
-- MAIN TABLES
-- =============================================

-- EI Cases table (main entity)
CREATE TABLE ei_cases (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Tracking information
    cra_tracking_no VARCHAR(50) UNIQUE NOT NULL,
    
    -- Atoll-controlled fields (immutable after create)
    site VARCHAR(50) NOT NULL,
    region VARCHAR(20) NOT NULL,
    province VARCHAR(50) NOT NULL,
    cra_region VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180 AND longitude <= 180),
    
    -- User-editable fields
    technology technology_enum NOT NULL,
    band_type band_type_enum NOT NULL,
    detection_datetime TIMESTAMPTZ NOT NULL,
    mvo_raise_datetime TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    date_of_clear_datetime TIMESTAMPTZ NULL,
    
    -- Frequency ranges (MHz)
    mtn_frequency_range_from INTEGER NOT NULL CHECK (mtn_frequency_range_from >= 0 AND mtn_frequency_range_from <= 6000),
    mtn_frequency_range_to INTEGER NOT NULL CHECK (mtn_frequency_range_to >= 0 AND mtn_frequency_range_to <= 6000),
    mtni_affected_frequency_range_from INTEGER NOT NULL CHECK (mtni_affected_frequency_range_from >= 0 AND mtni_affected_frequency_range_from <= 6000),
    mtni_affected_frequency_range_to INTEGER NOT NULL CHECK (mtni_affected_frequency_range_to >= 0 AND mtni_affected_frequency_range_to <= 6000),
    
    -- Optional source location
    source_location_lat DOUBLE PRECISION NULL CHECK (source_location_lat >= -90 AND source_location_lat <= 90),
    source_location_lng DOUBLE PRECISION NULL CHECK (source_location_lng >= -180 AND source_location_lng <= 180),
    
    -- Additional fields
    evidence_link TEXT NOT NULL,
    mvo_status mvo_status_enum NOT NULL,
    mvo_comment TEXT NULL,
    more_sites_text TEXT NULL,
    
    -- Soft delete fields
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ NULL,
    deleted_by VARCHAR(255) NULL,
    
    -- Audit fields
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modified_by VARCHAR(255) NOT NULL,
    modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_frequency_ranges CHECK (
        mtn_frequency_range_from < mtn_frequency_range_to AND
        mtni_affected_frequency_range_from < mtni_affected_frequency_range_to
    ),
    CONSTRAINT chk_detection_datetime CHECK (detection_datetime <= NOW()),
    CONSTRAINT chk_clear_datetime CHECK (
        date_of_clear_datetime IS NULL OR 
        (date_of_clear_datetime <= NOW() AND date_of_clear_datetime >= detection_datetime)
    ),
    CONSTRAINT chk_soft_delete CHECK (
        (is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL) OR
        (is_deleted = TRUE AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL)
    )
);

-- Case Comments table
CREATE TABLE case_comments (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Foreign key to case
    case_id INTEGER NOT NULL REFERENCES ei_cases(id) ON DELETE CASCADE,
    
    -- Comment content
    text TEXT NOT NULL,
    
    -- CRA metadata (pass-through)
    cra_cdate TIMESTAMPTZ NULL,
    cra_comment TEXT NULL,
    cra_status VARCHAR(100) NULL,
    
    -- Audit fields (create-only)
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Case Tests table
CREATE TABLE case_tests (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Foreign key to case
    case_id INTEGER NOT NULL REFERENCES ei_cases(id) ON DELETE CASCADE,
    
    -- Test information
    mvo_test_date TIMESTAMPTZ NOT NULL,
    mvo_test_comment TEXT NOT NULL,
    
    -- Audit fields (updatable)
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modified_by VARCHAR(255) NOT NULL,
    modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================
-- NOTE: Cells and Bands data comes from Atoll APIs
-- =============================================
-- The cells and bands data is fetched from Atoll APIs at runtime
-- and is not stored in the EI Tracker database. This data is:
-- - Validated against Atoll during case creation/update
-- - Retrieved from Atoll APIs when needed for display
-- - Not persisted locally to avoid data synchronization issues

-- =============================================
-- AUDIT AND CHANGE LOG TABLES
-- =============================================

-- Change log for EI cases (for export functionality)
CREATE TABLE ei_case_changes (
    id SERIAL PRIMARY KEY,
    case_id INTEGER NOT NULL REFERENCES ei_cases(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT NULL,
    new_value TEXT NULL,
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('CREATE', 'UPDATE', 'DELETE'))
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- Primary indexes for ei_cases
CREATE INDEX idx_ei_cases_site ON ei_cases(site);
CREATE INDEX idx_ei_cases_region ON ei_cases(region);
CREATE INDEX idx_ei_cases_province ON ei_cases(province);
CREATE INDEX idx_ei_cases_cra_region ON ei_cases(cra_region);
CREATE INDEX idx_ei_cases_city ON ei_cases(city);
CREATE INDEX idx_ei_cases_technology ON ei_cases(technology);
CREATE INDEX idx_ei_cases_band_type ON ei_cases(band_type);
CREATE INDEX idx_ei_cases_mvo_status ON ei_cases(mvo_status);
CREATE INDEX idx_ei_cases_detection_datetime ON ei_cases(detection_datetime);
CREATE INDEX idx_ei_cases_created_at ON ei_cases(created_at);
CREATE INDEX idx_ei_cases_modified_at ON ei_cases(modified_at);
CREATE INDEX idx_ei_cases_is_deleted ON ei_cases(is_deleted);
CREATE INDEX idx_ei_cases_cra_tracking_no ON ei_cases(cra_tracking_no);

-- Composite indexes for common queries
CREATE INDEX idx_ei_cases_region_status ON ei_cases(region, mvo_status) WHERE is_deleted = FALSE;
CREATE INDEX idx_ei_cases_detection_date_status ON ei_cases(detection_datetime, mvo_status) WHERE is_deleted = FALSE;
CREATE INDEX idx_ei_cases_technology_band_type ON ei_cases(technology, band_type) WHERE is_deleted = FALSE;

-- Geographic indexes
CREATE INDEX idx_ei_cases_location ON ei_cases USING GIST (
    ST_Point(longitude, latitude)
) WHERE is_deleted = FALSE;

-- Indexes for case_comments
CREATE INDEX idx_case_comments_case_id ON case_comments(case_id);
CREATE INDEX idx_case_comments_created_at ON case_comments(created_at);

-- Indexes for case_tests
CREATE INDEX idx_case_tests_case_id ON case_tests(case_id);
CREATE INDEX idx_case_tests_mvo_test_date ON case_tests(mvo_test_date);
CREATE INDEX idx_case_tests_created_at ON case_tests(created_at);

-- Note: No indexes needed for cells/bands as they come from Atoll APIs

-- Indexes for change log
CREATE INDEX idx_ei_case_changes_case_id ON ei_case_changes(case_id);
CREATE INDEX idx_ei_case_changes_changed_at ON ei_case_changes(changed_at);
CREATE INDEX idx_ei_case_changes_change_type ON ei_case_changes(change_type);

-- =============================================
-- TRIGGERS FOR AUDIT AND AUTOMATIC UPDATES
-- =============================================

-- Function to update modified_at timestamp
CREATE OR REPLACE FUNCTION update_modified_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for ei_cases modified_at
CREATE TRIGGER trigger_ei_cases_modified_at
    BEFORE UPDATE ON ei_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_at();

-- Trigger for case_tests modified_at
CREATE TRIGGER trigger_case_tests_modified_at
    BEFORE UPDATE ON case_tests
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_at();

-- Function to log changes
CREATE OR REPLACE FUNCTION log_ei_case_changes()
RETURNS TRIGGER AS $$
DECLARE
    field_name TEXT;
    old_val TEXT;
    new_val TEXT;
BEGIN
    -- Handle INSERT
    IF TG_OP = 'INSERT' THEN
        INSERT INTO ei_case_changes (case_id, field_name, old_value, new_value, changed_by, change_type)
        VALUES (NEW.id, 'RECORD_CREATED', NULL, 'Case created', NEW.created_by, 'CREATE');
        RETURN NEW;
    END IF;
    
    -- Handle UPDATE
    IF TG_OP = 'UPDATE' THEN
        -- Check each field for changes
        FOR field_name IN SELECT column_name FROM information_schema.columns 
                         WHERE table_name = 'ei_cases' AND column_name NOT IN ('id', 'created_at', 'modified_at') LOOP
            EXECUTE format('SELECT ($1).%I, ($2).%I', field_name, field_name) INTO old_val, new_val USING OLD, NEW;
            
            IF old_val IS DISTINCT FROM new_val THEN
                INSERT INTO ei_case_changes (case_id, field_name, old_value, new_value, changed_by, change_type)
                VALUES (NEW.id, field_name, old_val::TEXT, new_val::TEXT, NEW.modified_by, 'UPDATE');
            END IF;
        END LOOP;
        RETURN NEW;
    END IF;
    
    -- Handle DELETE (soft delete)
    IF TG_OP = 'DELETE' THEN
        INSERT INTO ei_case_changes (case_id, field_name, old_value, new_value, changed_by, change_type)
        VALUES (OLD.id, 'RECORD_DELETED', 'Case deleted', NULL, OLD.deleted_by, 'DELETE');
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for change logging
CREATE TRIGGER trigger_ei_case_changes
    AFTER INSERT OR UPDATE OR DELETE ON ei_cases
    FOR EACH ROW
    EXECUTE FUNCTION log_ei_case_changes();

-- =============================================
-- VIEWS FOR COMMON QUERIES
-- =============================================

-- View for active cases with computed age
CREATE VIEW active_ei_cases AS
SELECT 
    c.*,
    CASE 
        WHEN c.mvo_status IN ('Solved by CRA', 'Resolved automatically') THEN
            EXTRACT(EPOCH FROM (c.date_of_clear_datetime - c.detection_datetime)) / 86400
        ELSE
            EXTRACT(EPOCH FROM (NOW() - c.detection_datetime)) / 86400
    END::INTEGER AS age
FROM ei_cases c
WHERE c.is_deleted = FALSE;

-- View for case statistics
CREATE VIEW case_statistics AS
SELECT 
    region,
    province,
    cra_region,
    mvo_status,
    COUNT(*) as case_count,
    AVG(EXTRACT(EPOCH FROM (NOW() - detection_datetime)) / 86400)::INTEGER as avg_age_days
FROM ei_cases
WHERE is_deleted = FALSE
GROUP BY region, province, cra_region, mvo_status;

-- =============================================
-- FUNCTIONS FOR BUSINESS LOGIC
-- =============================================

-- Function to generate CRA tracking number
CREATE OR REPLACE FUNCTION generate_cra_tracking_no()
RETURNS TEXT AS $$
BEGIN
    RETURN 'EI_' || TO_CHAR(NOW() AT TIME ZONE 'Asia/Tehran', 'YYYYMMDDHH24MISS');
END;
$$ LANGUAGE plpgsql;

-- Function to validate frequency ranges
CREATE OR REPLACE FUNCTION validate_frequency_ranges(
    mtn_from INTEGER,
    mtn_to INTEGER,
    mtni_from INTEGER,
    mtni_to INTEGER
)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (
        mtn_from >= 0 AND mtn_from < mtn_to AND mtn_to <= 6000 AND
        mtni_from >= 0 AND mtni_from < mtni_to AND mtni_to <= 6000
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get case age
CREATE OR REPLACE FUNCTION get_case_age(case_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    case_record ei_cases%ROWTYPE;
    age_days INTEGER;
BEGIN
    SELECT * INTO case_record FROM ei_cases WHERE id = case_id AND is_deleted = FALSE;
    
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    IF case_record.mvo_status IN ('Solved by CRA', 'Resolved automatically') THEN
        age_days := EXTRACT(EPOCH FROM (case_record.date_of_clear_datetime - case_record.detection_datetime)) / 86400;
    ELSE
        age_days := EXTRACT(EPOCH FROM (NOW() - case_record.detection_datetime)) / 86400;
    END IF;
    
    RETURN age_days::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- SAMPLE DATA (for testing)
-- =============================================

-- Insert sample EI case
INSERT INTO ei_cases (
    cra_tracking_no, site, region, province, cra_region, city, latitude, longitude,
    technology, band_type, detection_datetime, mvo_raise_datetime,
    mtn_frequency_range_from, mtn_frequency_range_to,
    mtni_affected_frequency_range_from, mtni_affected_frequency_range_to,
    evidence_link, mvo_status, created_by, modified_by
) VALUES (
    generate_cra_tracking_no(),
    'IR-TEH-12345',
    'R2',
    'Tehran',
    'north_west',
    'Tehran',
    35.6892,
    51.3890,
    'LTE',
    'ULBand',
    '2025-09-02T10:30:00+03:30'::TIMESTAMPTZ,
    NOW(),
    1805,
    1815,
    1800,
    1820,
    'https://evidence.example/tool/123',
    'Open, Under Investigation by CRA',
    'example.user@mtnirancell.ir',
    'example.user@mtnirancell.ir'
);

-- Note: Cells and bands data comes from Atoll APIs, not stored locally

-- Insert sample comment
INSERT INTO case_comments (case_id, text, created_by) VALUES (
    1,
    'On-site spectrum check scheduled.',
    'example.user@mtnirancell.ir'
);

-- Insert sample test
INSERT INTO case_tests (case_id, mvo_test_date, mvo_test_comment, created_by, modified_by) VALUES (
    1,
    '2025-09-01T09:00:00+03:30'::TIMESTAMPTZ,
    'External source near 1800 MHz.',
    'example.user@mtnirancell.ir',
    'example.user@mtnirancell.ir'
);

-- =============================================
-- COMMENTS AND DOCUMENTATION
-- =============================================

COMMENT ON TABLE ei_cases IS 'Main table for EI interference cases. Atoll-controlled fields are immutable after creation.';
COMMENT ON TABLE case_comments IS 'Comments on EI cases. Comments are not editable or deletable after creation.';
COMMENT ON TABLE case_tests IS 'Test records for EI cases. Tests can be updated but not deleted.';
-- Note: case_cells and case_bands tables removed - data comes from Atoll APIs
COMMENT ON TABLE ei_case_changes IS 'Audit log for all changes to EI cases, used for export functionality.';

COMMENT ON COLUMN ei_cases.cra_tracking_no IS 'Auto-generated tracking number in format EI_YYYYMMDDHH24MISS';
COMMENT ON COLUMN ei_cases.site IS 'Site ID from Atoll - immutable after creation';
COMMENT ON COLUMN ei_cases.cells IS 'Array of cell IDs - fetched from Atoll APIs at runtime';
COMMENT ON COLUMN ei_cases.bands IS 'Array of bands - fetched from Atoll APIs at runtime';
COMMENT ON COLUMN ei_cases.detection_datetime IS 'When interference was detected - must be <= now';
COMMENT ON COLUMN ei_cases.mvo_raise_datetime IS 'Auto-set on case creation';
COMMENT ON COLUMN ei_cases.date_of_clear_datetime IS 'When case was resolved - must be >= detection_datetime';
COMMENT ON COLUMN ei_cases.is_deleted IS 'Soft delete flag - when true, case is considered deleted';
COMMENT ON COLUMN ei_cases.age IS 'Computed field - days since detection or resolution';

-- =============================================
-- GRANTS AND PERMISSIONS (adjust as needed)
-- =============================================

-- Example grants (adjust based on your security model)
-- GRANT SELECT, INSERT, UPDATE ON ei_cases TO ei_tracker_app;
-- GRANT SELECT, INSERT ON case_comments TO ei_tracker_app;
-- GRANT SELECT, INSERT, UPDATE ON case_tests TO ei_tracker_app;
-- Note: No grants needed for case_cells/case_bands as they don't exist (data from Atoll APIs)
-- GRANT SELECT ON ei_case_changes TO ei_tracker_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ei_tracker_app;
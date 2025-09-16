# EI Tracker Database Design

## Overview

This document describes the comprehensive database design for the EI Tracker system based on the OpenAPI specification v1.1.2. The design follows PostgreSQL best practices with proper normalization, constraints, indexes, and audit mechanisms.

## Database Schema Summary

### Core Tables

1. **ei_cases** - Main entity for EI interference cases
2. **case_comments** - Comments on cases (create-only, no updates/deletes)
3. **case_tests** - Test records for cases (updatable, no deletes)
4. **case_cells** - Junction table for case-to-cell relationships
5. **case_bands** - Junction table for case-to-band relationships
6. **ei_case_changes** - Audit log for all case changes

### Key Design Principles

- **Immutable Atoll Fields**: Site, region, province, cra_region, city, latitude, longitude, and cells are immutable after creation
- **Soft Delete**: Cases are soft-deleted with audit trail
- **Comprehensive Audit**: All changes are logged with timestamps and user information
- **Performance Optimized**: Strategic indexes for common query patterns
- **Data Integrity**: Extensive constraints and validation rules

## Table Relationships

```
ei_cases (1) -----> (N) case_comments
ei_cases (1) -----> (N) case_tests
ei_cases (1) -----> (N) case_cells
ei_cases (1) -----> (N) case_bands
ei_cases (1) -----> (N) ei_case_changes
```

## Detailed Table Specifications

### 1. ei_cases (Main Entity)

**Purpose**: Stores EI interference cases with all required fields from the API specification.

**Key Features**:
- Auto-generated CRA tracking number
- Immutable Atoll-controlled fields after creation
- Comprehensive validation constraints
- Soft delete mechanism
- Full audit trail

**Notable Constraints**:
- Frequency ranges must be valid (0-6000 MHz, from < to)
- Detection datetime must be ≤ now
- Clear datetime must be ≥ detection datetime
- Geographic coordinates within valid ranges
- Soft delete consistency checks

### 2. case_comments

**Purpose**: Stores comments on cases. Comments are create-only (no updates or deletes).

**Key Features**:
- Foreign key to ei_cases with CASCADE delete
- CRA metadata fields for pass-through data
- Audit fields (create-only)

### 3. case_tests

**Purpose**: Stores test records for cases. Tests can be updated but not deleted.

**Key Features**:
- Foreign key to ei_cases with CASCADE delete
- Full audit trail (created and modified)
- Test date and comment fields

### 4. Junction Tables

**case_cells**: Many-to-many relationship between cases and cell IDs
**case_bands**: Many-to-many relationship between cases and frequency bands

### 5. ei_case_changes

**Purpose**: Comprehensive audit log for all changes to cases.

**Key Features**:
- Tracks field-level changes
- Records old and new values
- Change type classification (CREATE, UPDATE, DELETE)
- Used for export functionality

## Data Types and Enums

### Enumerations
- **band_type_enum**: 'ULBand', 'DLBand'
- **mvo_status_enum**: All MVO status values from API spec
- **technology_enum**: 'GSM', 'UMTS', 'LTE', 'NR'
- **band_enum**: '900', '1800', '2100', '2300', '2600', '3500'

### Special Data Types
- **TIMESTAMPTZ**: All datetime fields with timezone support
- **DOUBLE PRECISION**: Geographic coordinates and frequency ranges
- **TEXT**: For large text fields (comments, evidence links)

## Indexes and Performance

### Primary Indexes
- All foreign keys
- All filterable fields (region, province, technology, etc.)
- Date/time fields for sorting and filtering
- Soft delete flag for active record queries

### Composite Indexes
- Region + MVO status (common filter combination)
- Detection date + MVO status (for age calculations)
- Technology + band type (for technology-specific queries)

### Geographic Index
- GIST index on latitude/longitude for spatial queries

## Business Logic Functions

### 1. generate_cra_tracking_no()
Generates unique tracking numbers in format: EI_YYYYMMDDHH24MISS

### 2. validate_frequency_ranges()
Validates that frequency ranges are within valid bounds and properly ordered

### 3. get_case_age()
Calculates case age in days based on MVO status and resolution date

## Audit and Change Tracking

### Automatic Triggers
- **modified_at**: Updates timestamp on any record modification
- **change_logging**: Records all field-level changes in ei_case_changes table

### Change Types
- **CREATE**: New record creation
- **UPDATE**: Field modifications
- **DELETE**: Soft delete operations

## Views for Common Queries

### 1. active_ei_cases
- Filters out soft-deleted cases
- Includes computed age field
- Aggregates cells and bands arrays

### 2. case_statistics
- Provides aggregated statistics by region, province, and status
- Calculates average age for reporting

## Security Considerations

### Data Protection
- Soft delete prevents accidental data loss
- Comprehensive audit trail for compliance
- Foreign key constraints maintain referential integrity

### Access Control
- Role-based access should be implemented at application level
- Database grants should follow principle of least privilege
- Sensitive operations should be logged

## Integration Points

### External Systems
- **Atoll**: Validates site, cell, and band data
- **Keycloak**: Provides user authentication and authorization
- **File Service**: Handles export file generation and downloads

### API Compatibility
- All fields from OpenAPI specification are supported
- Computed fields (age) are calculated in views
- Timezone handling supports Asia/Tehran (UTC+03:30)

## Migration and Deployment

### Initial Setup
1. Create enums and types
2. Create main tables with constraints
3. Create junction tables
4. Create audit tables
5. Add indexes for performance
6. Create triggers for automation
7. Create views for common queries
8. Add business logic functions

### Sample Data
- Includes test data for development and testing
- Demonstrates proper relationships and constraints

## Maintenance and Monitoring

### Performance Monitoring
- Monitor index usage and query performance
- Track audit table growth and archival needs
- Monitor soft-deleted record cleanup

### Data Maintenance
- Regular cleanup of old audit records
- Archive of completed cases
- Backup and recovery procedures

## Future Enhancements

### Potential Improvements
- Partitioning for large datasets
- Materialized views for complex aggregations
- Full-text search capabilities
- Advanced geographic indexing
- Automated data archival policies

This database design provides a robust foundation for the EI Tracker system while maintaining data integrity, performance, and auditability requirements.
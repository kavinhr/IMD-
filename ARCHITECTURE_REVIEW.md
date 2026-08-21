# Weather Data Management System (WDMS)
# Architecture & Design Review Document

**Project**: Weather Data Management System  
**Organization**: Regional Meteorological Centre, IMD Chennai  
**Document Version**: 1.0  
**Date**: June 2026  
**Reviewed By**: Principal Software Architect

---

## EXECUTIVE SUMMARY

This document provides a comprehensive architectural review and design analysis for the Weather Data Management System (WDMS) before implementation. The system aims to replace manual Excel-based workflows with a centralized PostgreSQL database solution serving 16+ meteorological stations across Tamil Nadu.

**Critical Success Factors Identified:**
1. Data quality and integrity during migration
2. Long-term scalability (10+ year lifespan)
3. Performance with growing datasets
4. Security for government data
5. User adoption and ease of use

---

## 1. SYSTEM ARCHITECTURE ANALYSIS

### 1.1 Proposed Architecture

```
┌─────────────────────────────────────────────────────┐
│         PRESENTATION LAYER (Web Browser)            │
│  Bootstrap 5 | DataTables | Chart.js | jQuery      │
└─────────────────────────────────────────────────────┘
                        ↕ HTTP/HTTPS
┌─────────────────────────────────────────────────────┐
│          APPLICATION LAYER (Flask App)              │
│  Routes | Services | Business Logic | Validation   │
└─────────────────────────────────────────────────────┘
                        ↕ SQLAlchemy ORM
┌─────────────────────────────────────────────────────┐
│         DATA LAYER (PostgreSQL 14+)                 │
│  Core | Security | Quality | Archive | Audit        │
└─────────────────────────────────────────────────────┘
                        ↕ File System
┌─────────────────────────────────────────────────────┐
│         STORAGE LAYER                               │
│  Excel Archive | Exports | Backups | Logs          │
└─────────────────────────────────────────────────────┘
```

### 1.2 Architectural Strengths ✅


**1. Clear Separation of Concerns**
- Presentation, application, data, and storage layers well-defined
- Easy to maintain and test individual components
- Aligns with best practices for enterprise applications

**2. Technology Stack Alignment**
- PostgreSQL: Proven reliability for government applications
- Flask: Lightweight yet powerful for internal applications
- Bootstrap: Responsive UI without heavy frontend framework overhead
- All technologies have long-term support and active communities

**3. Scalability Path**
- Database schema supports partitioning for future growth
- Service layer can be extracted to microservices if needed
- Stateless application layer enables horizontal scaling

**4. Security-First Design**
- Role-based access control (RBAC)
- Audit logging at database level
- Session management and password policies
- Prepared statements via ORM (SQL injection prevention)

### 1.3 Architectural Risks ⚠️

**RISK 1: Single Point of Failure**
- **Issue**: Monolithic application with single database
- **Impact**: If database server fails, entire system unavailable
- **Mitigation**: 
  - Implement PostgreSQL streaming replication (Primary-Standby)
  - Set up automated failover using pg_auto_failover
  - Regular backup testing (monthly)

**RISK 2: No Caching Layer**
- **Issue**: Repeated queries for dashboard, reports hit database directly
- **Impact**: Performance degradation as data grows (1M+ records)
- **Mitigation**:
  - Implement Redis for session storage and query results
  - Use PostgreSQL materialized views for aggregate statistics
  - Add @cache decorators on frequently accessed data


**RISK 3: Limited Concurrency Handling**
- **Issue**: Flask development server not production-ready
- **Impact**: Poor performance with multiple simultaneous users (10+)
- **Mitigation**:
  - Deploy with Gunicorn (4-8 workers based on CPU cores)
  - Use Nginx as reverse proxy
  - Connection pooling in SQLAlchemy (pool_size=20, max_overflow=40)

**RISK 4: Data Migration Complexity**
- **Issue**: Excel files have inconsistent formats, typos, missing data
- **Impact**: Migration failures, data loss, incorrect values
- **Mitigation**:
  - Implement comprehensive ETL validation
  - Create staging tables for review before final commit
  - Dry-run mode with detailed error reporting
  - Manual review workflow for problematic records

**RISK 5: No Real-time Backup Verification**
- **Issue**: Backups may be corrupted without detection
- **Impact**: Cannot restore during disaster
- **Mitigation**:
  - Implement backup verification script
  - Test restore monthly on separate test database
  - Store backups on separate physical drive/NAS
  - Keep 30 days of backups (daily) + monthly archives

---

## 2. DATABASE DESIGN ANALYSIS

### 2.1 Schema Design Review

**Proposed Schema Structure:**
```
core schema:     stations, parameters, observations, parameter_station
security schema: users, roles, user_sessions
quality schema:  data_quality_issues, validation_rules, data_completeness
archive schema:  excel_files, migration_history
audit schema:    audit_logs
```

### 2.2 Database Strengths ✅


**1. Normalized Design**
- 3NF normalization prevents data redundancy
- Lookup tables (stations, parameters) separate from transactional data
- Many-to-many relationship (parameter_station) properly handled

**2. Flexible Schema Design**
- JSONB columns for metadata allow schema evolution
- Supports adding new parameters without schema changes
- Future-proof for AI/ML feature storage

**3. Comprehensive Constraints**
- CHECK constraints for data validation (year range, month 1-12)
- UNIQUE constraints prevent duplicates (station+parameter+year+month)
- Foreign keys maintain referential integrity

**4. Performance Optimization**
- Proper indexing on query columns (station_id, parameter_id, year, month)
- Composite indexes for common query patterns
- GIST index for geospatial queries (future use)

### 2.3 Database Risks & Improvements ⚠️

**ISSUE 1: Observations Table Growth**
- **Problem**: Single table for all observations will grow large
  - 16 stations × 14 parameters × 40 years × 12 months = ~107,000 records
  - With monthly additions: +2,688 records/year
  - In 10 years: ~134,000 records (manageable but consider partitioning)
  
- **Recommendation**: Implement declarative partitioning
  ```sql
  -- Partition by year for better query performance
  CREATE TABLE observations_2020 PARTITION OF observations
  FOR VALUES FROM (2020) TO (2021);
  ```


**ISSUE 2: Missing Data Representation**
- **Problem**: Three ways to represent missing data:
  - NULL in obs_value
  - "***" in value_text
  - "MISSING" in data_quality_flag
  
- **Recommendation**: Standardize approach
  ```
  Rule: NULL obs_value always means no data
  value_text stores original notation ("***", "TR", etc.)
  data_quality_flag indicates reason ("MISSING", "TRACE", "ERROR")
  ```

**ISSUE 3: Audit Log Growth**
- **Problem**: audit_logs table will grow indefinitely
  - Every INSERT/UPDATE/DELETE logged
  - Can reach millions of records in 10 years
  
- **Recommendation**: 
  - Partition audit_logs by month
  - Archive logs older than 2 years to separate table
  - Implement automated archival job

**ISSUE 4: No Database-Level Constraints for Parameter Ranges**
- **Problem**: Parameter min/max values stored but not enforced
  - Temperature could be entered as 500°C
  - Rainfall could be negative
  
- **Recommendation**: Add trigger-based validation
  ```sql
  CREATE TRIGGER validate_observation_value
  BEFORE INSERT OR UPDATE ON observations
  FOR EACH ROW
  EXECUTE FUNCTION check_parameter_range();
  ```

**ISSUE 5: Insufficient Indexes for Reports**
- **Problem**: Missing composite indexes for common report queries
  
- **Recommendation**: Add reporting-specific indexes
  ```sql
  -- For monthly trend reports
  CREATE INDEX idx_obs_monthly_trend 
  ON observations(parameter_id, obs_year, obs_month, obs_value)
  WHERE obs_value IS NOT NULL;
  
  -- For station comparison reports
  CREATE INDEX idx_obs_station_comparison
  ON observations(parameter_id, obs_year, obs_month, station_id, obs_value);
  ```


---

## 3. ETL (EXTRACT-TRANSFORM-LOAD) ANALYSIS

### 3.1 Data Migration Challenges

**CHALLENGE 1: Inconsistent Excel Formats**
Based on provided files (ARP-MAST.xls, CMB-MAST.xlsx):

```
Issues Found:
1. Typos: "25..3" instead of "25.3" (2017 data)
2. Mixed notations: "0 21.0" (space instead of decimal)
3. Special markers: "***", "TR", "trace", "0"
4. Embedded dates: "4 (07)" means value 4 on 7th day
5. Missing data: Entire years (2023) or partial years (2022: Jan-Mar only)
6. Format changes: Some files have MAX/MIN rows, others don't
7. Notes in data cells: "for DDGM", "instrument unserviceable"
8. Variable element counts: 14 elements vs 17 elements
```

**CHALLENGE 2: Data Quality Detection**

Current data contains:
- Missing years in sequence (1983-2022 ✓, 2023 ✗, 2024 ✓)
- Partial year data (2022: only 3 months)
- Instrument failures (marked as ***)
- Trace values (TR, trace, 0.0)
- Outliers (potential data entry errors)

### 3.2 Recommended ETL Architecture

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: EXTRACT (Excel Parser)                        │
│  - Read workbook structure                              │
│  - Identify sheets and parameter mappings               │
│  - Extract raw data with position metadata              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: VALIDATE (Quality Checks)                     │
│  - Check station exists in database                     │
│  - Verify parameter mappings                            │
│  - Detect data type mismatches                          │
│  - Flag outliers and anomalies                          │
│  - Identify missing data patterns                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: TRANSFORM (Data Cleaning)                     │
│  - Normalize special values (TR → text, *** → NULL)     │
│  - Fix known typos ("25..3" → 25.3)                     │
│  - Parse embedded dates                                 │
│  - Convert units if needed                              │
│  - Generate quality flags                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 4: STAGE (Review Table)                          │
│  - Load into staging table                              │
│  - Generate migration report                            │
│  - Present to user for review                           │
│  - Allow selective import                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 5: LOAD (Final Import)                           │
│  - Insert into observations table                       │
│  - Log to migration_history                             │
│  - Update data_completeness                             │
│  - Generate quality issues records                      │
└─────────────────────────────────────────────────────────┘
```


### 3.3 ETL Risk Mitigation

**MITIGATION 1: Dry Run Mode**
```python
# Always run migration in dry-run first
etl_service.migrate(file, dry_run=True)
# Reviews results
# Then commit
etl_service.migrate(file, dry_run=False, commit=True)
```

**MITIGATION 2: Rollback Capability**
```sql
-- Use transaction savepoints
BEGIN;
SAVEPOINT before_migration;
-- ... perform migration ...
-- If issues found:
ROLLBACK TO SAVEPOINT before_migration;
```

**MITIGATION 3: Data Lineage**
```
Store in observations table:
- source_file: "ARP-MAST.xls"
- source_sheet: "Element 1"
- source_row: 15
- source_column: "MAR"
Enables tracing back to original Excel file
```

**MITIGATION 4: Incremental Import**
```
Allow importing by:
- One parameter at a time
- One year range at a time
- One station at a time
Prevents massive failures affecting all data
```

---

## 4. SECURITY ARCHITECTURE ANALYSIS

### 4.1 Security Strengths ✅

**1. Authentication & Authorization**
- Password hashing with Werkzeug (PBKDF2-SHA256)
- Role-based access control (4 roles)
- Session management with Flask-Login
- Account lockout after failed attempts

**2. Data Protection**
- SQL injection prevention via ORM
- XSS protection via Jinja2 auto-escaping
- CSRF tokens on all forms
- Secure session cookies

**3. Audit Trail**
- All data modifications logged
- User actions tracked
- IP address and timestamp recorded


### 4.2 Security Gaps ⚠️

**GAP 1: No Password Complexity Validation**
- **Issue**: Config specifies requirements but no enforcement code
- **Fix**: Implement password validator
  ```python
  def validate_password(password):
      if len(password) < 8:
          return False
      if not any(c.isupper() for c in password):
          return False
      if not any(c.islower() for c in password):
          return False
      if not any(c.isdigit() for c in password):
          return False
      return True
  ```

**GAP 2: No Rate Limiting**
- **Issue**: API endpoints vulnerable to brute force
- **Fix**: Implement Flask-Limiter
  ```python
  from flask_limiter import Limiter
  limiter = Limiter(app, key_func=get_remote_address)
  
  @limiter.limit("5 per minute")
  @app.route("/login")
  def login():
      pass
  ```

**GAP 3: Sensitive Data in Logs**
- **Issue**: May log passwords, tokens accidentally
- **Fix**: Implement log sanitization
  ```python
  SENSITIVE_FIELDS = ['password', 'token', 'secret']
  def sanitize_log(data):
      for field in SENSITIVE_FIELDS:
          if field in data:
              data[field] = '***REDACTED***'
      return data
  ```

**GAP 4: No Input Sanitization**
- **Issue**: File uploads could contain malicious content
- **Fix**: Validate file types and scan uploads
  ```python
  ALLOWED_EXTENSIONS = {'.xls', '.xlsx'}
  MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
  
  def validate_upload(file):
      # Check extension
      # Check magic bytes
      # Scan for macros
      pass
  ```

**GAP 5: No Encryption at Rest**
- **Issue**: Database files not encrypted
- **Recommendation**: For government data, consider:
  - PostgreSQL transparent data encryption (TDE)
  - Or OS-level encryption (BitLocker on Windows)
  - Encrypt backups before storing


---

## 5. PERFORMANCE ANALYSIS

### 5.1 Expected Query Patterns

**Pattern 1: Time Series Queries (Most Common)**
```sql
-- Get temperature for Chennai, 1990-2025
SELECT obs_year, obs_month, obs_value
FROM observations
WHERE station_id = 1 AND parameter_id = 5
AND obs_year BETWEEN 1990 AND 2025
ORDER BY obs_year, obs_month;
```
**Performance**: ~36 years × 12 months = 432 rows  
**Time**: < 10ms with proper indexes ✅

**Pattern 2: Multi-Station Comparison**
```sql
-- Compare rainfall across all 16 stations for 2024
SELECT s.station_name, o.obs_month, o.obs_value
FROM observations o
JOIN stations s ON o.station_id = s.station_id
WHERE o.parameter_id = 11 AND o.obs_year = 2024
ORDER BY s.station_name, o.obs_month;
```
**Performance**: 16 stations × 12 months = 192 rows  
**Time**: < 50ms with indexes ✅

**Pattern 3: Aggregate Statistics**
```sql
-- Calculate average temperature per year
SELECT obs_year, AVG(obs_value) as avg_temp
FROM observations
WHERE station_id = 1 AND parameter_id = 1
GROUP BY obs_year
ORDER BY obs_year;
```
**Performance**: Scan ~500 rows, aggregate 40 years  
**Time**: < 100ms ✅ (but could benefit from materialized view)

**Pattern 4: Data Quality Report**
```sql
-- Find all missing data
SELECT COUNT(*)
FROM observations
WHERE obs_value IS NULL OR value_text IN ('***', 'missing');
```
**Performance**: Full table scan on 134,000 rows  
**Time**: 200-500ms ⚠️ (needs optimization)

### 5.2 Performance Bottlenecks

**BOTTLENECK 1: Dashboard Loading**
- **Issue**: Dashboard shows multiple widgets with aggregated data
- **Impact**: 5-10 queries on page load, each 100-300ms
- **Solution**: 
  - Create materialized view for dashboard statistics
  - Refresh daily via cron job
  - Load time: < 100ms total ✅


**BOTTLENECK 2: Report Generation**
- **Issue**: Yearly reports query 12 months × 14 parameters = 168 values
- **Impact**: Complex joins, multiple queries
- **Solution**:
  - Use single optimized query with JSON aggregation
  - Cache frequently accessed reports (last 3 years)
  - Generate reports asynchronously for large date ranges

**BOTTLENECK 3: Excel Export**
- **Issue**: Exporting 10,000+ rows to Excel takes time
- **Impact**: Browser timeout, user frustration
- **Solution**:
  - Implement background job queue (Celery/RQ)
  - Email download link when ready
  - Or implement streaming response

**BOTTLENECK 4: Search with Multiple Filters**
- **Issue**: OR queries across parameters slow without proper indexes
- **Impact**: Search for "all temperature parameters" scans multiple indexes
- **Solution**:
  - Add GIN index on parameter category
  - Use parameter groups for common searches
  - Limit results to 10,000 rows

### 5.3 Recommended Optimizations

**OPTIMIZATION 1: Connection Pooling**
```python
# config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 40,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

**OPTIMIZATION 2: Query Result Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_station_parameters(station_id):
    # Cached for 1 hour
    return db.session.query(Parameter).join(...).all()
```

**OPTIMIZATION 3: Pagination**
```python
# Always paginate large result sets
results = query.paginate(page=page, per_page=50, error_out=False)
```

**OPTIMIZATION 4: Lazy Loading**
```python
# Use selectinload for N+1 query prevention
observations = db.session.query(Observation)\
    .options(selectinload(Observation.station))\
    .options(selectinload(Observation.parameter))\
    .all()
```


---

## 6. SCALABILITY ASSESSMENT

### 6.1 Current System Capacity

**Database Size Projection:**
```
Current State (Year 0):
- 16 stations × 14 parameters × 40 years × 12 months = 107,520 records
- Average row size: ~200 bytes
- Total data: ~21 MB

After 10 Years (Year 10):
- Additional records: 16 × 14 × 10 × 12 = 26,880 records
- Total records: 134,400
- Total data: ~27 MB

Conclusion: Database size is NOT a concern ✅
```

**Concurrent Users:**
```
Expected: 5-15 simultaneous users
Flask development server: 1 thread (INADEQUATE) ❌
Gunicorn with 4 workers: 20-40 concurrent requests (ADEQUATE) ✅
Nginx + Gunicorn + connection pooling: 100+ requests (EXCELLENT) ✅
```

### 6.2 Scalability Strategies

**STRATEGY 1: Vertical Scaling (Recommended for Phase 1)**
- Increase server RAM (8GB → 16GB)
- Faster SSD for database storage
- More CPU cores for Gunicorn workers
- Cost-effective for 10+ years

**STRATEGY 2: Read Replicas (If Needed)**
- Primary database for writes
- Read replica for reports and analytics
- Reduces load on primary database

**STRATEGY 3: Application Caching**
```
Add Redis layer:
- Session storage (off-load from database)
- Query result caching
- Rate limiting counters
```

**STRATEGY 4: Horizontal Scaling (Future)**
- If expanding to all India (500+ stations):
  - Shard database by region
  - Multiple application servers behind load balancer
  - Distributed caching

### 6.3 Storage Scalability

**Excel Archive Growth:**
```
Current: ~16 files × 2 MB = 32 MB
Annual growth: ~16 files × 200 KB = 3.2 MB/year
10-year projection: 32 MB + 32 MB = 64 MB

Recommendation: No special handling needed ✅
```

**Export Files:**
```
Assumption: 100 exports/month × 5 MB = 500 MB/month
Annual: 6 GB
Strategy: Auto-delete exports older than 30 days
```

**Backups:**
```
Daily backup size: ~100 MB (compressed)
30 days retention: 3 GB
Annual: 3 GB × 12 = 36 GB
Strategy: Move monthly backups to external NAS
```


---

## 7. USER EXPERIENCE ANALYSIS

### 7.1 Current Excel Workflow

**Steps to Find Data:**
1. Identify station (know code or name)
2. Locate correct Excel file (by browsing folders)
3. Open workbook (wait for Excel)
4. Find correct sheet (scroll through 14+ sheets)
5. Locate year row and month column
6. Manually copy value
7. Repeat for other stations/parameters

**Time**: 2-5 minutes per query  
**Error Rate**: High (wrong sheet, wrong cell, misread value)

### 7.2 Proposed WDMS Workflow

**Steps to Find Data:**
1. Open browser (already running)
2. Navigate to Search page
3. Select filters from dropdowns
4. Click Search button
5. View results in table
6. Export if needed

**Time**: 10-30 seconds per query ✅  
**Error Rate**: Minimal (validated dropdowns, no manual lookup)

**Improvement**: 10-30× faster, significantly fewer errors

### 7.3 UI/UX Recommendations

**RECOMMENDATION 1: Quick Search Widget**
```
Dashboard should have prominent search box:
"Find data for [Station ▼] [Parameter ▼] in [Year ▼]"
[Search Button]

Returns: Single value or table
Provides: 80% of use cases with one click
```

**RECOMMENDATION 2: Recent Searches**
```
Track last 10 searches per user
Display as quick links:
- "Chennai Temperature 2024" (5 min ago)
- "Coimbatore Rainfall 2023" (1 hour ago)

Benefit: Repeat queries instant
```

**RECOMMENDATION 3: Keyboard Shortcuts**
```
Ctrl+K: Open quick search
Ctrl+S: Save current view
Ctrl+E: Export current results
Ctrl+N: New observation entry

Benefit: Power users work faster
```

**RECOMMENDATION 4: Bulk Data Entry**
```
Instead of one-by-one entry:
Provide spreadsheet-like grid:
Month | JAN | FEB | MAR | ...
Value |  30 | 32  | 35  | ...

Benefit: Faster monthly data entry
```

**RECOMMENDATION 5: Data Quality Indicators**
```
Visual indicators in results:
🟢 Validated data
🟡 Estimated/interpolated data
🔴 Missing/suspicious data
⚪ Trace values

Benefit: Immediate quality assessment
```


---

## 8. DATA QUALITY STRATEGY

### 8.1 Quality Issues Classification

**CATEGORY 1: Missing Data**
```
Type A: Structural Missing (station not operational)
Example: Station X started in 1990, no data before 1990
Action: Mark as "NOT APPLICABLE", exclude from completeness %

Type B: Instrument Failure
Example: "***" in data, note says "instrument unserviceable"
Action: Mark as "MISSING", include in completeness %, flag for attention

Type C: Data Entry Gap
Example: 2023 completely missing, but 2024 exists
Action: Mark as "DATA GAP", high priority for recovery
```

**CATEGORY 2: Suspicious Values**
```
Type A: Out of Range
Example: Temperature = 150°C (physically impossible)
Action: Quarantine, require manual review

Type B: Unusual but Possible
Example: Rainfall = 500mm in one month (rare but possible)
Action: Flag for review, allow but mark

Type C: Data Entry Error
Example: "25..3" instead of "25.3"
Action: Auto-correct with confidence score, log correction
```

**CATEGORY 3: Trace Values**
```
Examples: "TR", "trace", "0.0" for rainfall
Meaning: Rainfall occurred but too small to measure (<0.1mm)
Action: Store as value_text="TR", obs_value=0, flag="TRACE"
```

### 8.2 Automated Quality Checks

**CHECK 1: Range Validation**
```python
parameter_ranges = {
    'temperature': (-20, 50),     # °C, Tamil Nadu climate
    'rainfall': (0, 1000),        # mm/month
    'humidity': (0, 100),         # %
    'wind_speed': (0, 150),       # km/h
    'pressure': (950, 1050)       # hPa
}

def validate_range(parameter, value):
    min_val, max_val = parameter_ranges[parameter.category]
    return min_val <= value <= max_val
```

**CHECK 2: Temporal Consistency**
```python
def check_temporal_anomaly(current, previous, next):
    # Sudden spike detection
    if previous and next:
        avg = (previous + next) / 2
        if abs(current - avg) > 3 * std_dev:
            return "POTENTIAL_SPIKE"
    return "OK"
```

**CHECK 3: Completeness Calculation**
```python
def calculate_completeness(station_id, parameter_id, year):
    expected_months = 12
    actual_months = count_non_null_observations()
    completeness = (actual_months / expected_months) * 100
    return completeness
```


### 8.3 Quality Dashboard Design

**Recommended Dashboard Layout:**
```
┌──────────────────────────────────────────────────────────┐
│  DATA QUALITY OVERVIEW                          📊       │
├──────────────────────────────────────────────────────────┤
│  Overall Completeness: 94.2% ████████████████▓░░░        │
│                                                          │
│  ⚠️  12 High Priority Issues                             │
│  🟡  45 Medium Priority Issues                           │
│  🟢  234 Low Priority Issues Resolved                    │
├──────────────────────────────────────────────────────────┤
│  Issues by Type                 | Issues by Station     │
│  - Missing Data: 78            | - Chennai: 12         │
│  - Outliers: 15                | - Coimbatore: 8       │
│  - Duplicates: 4               | - Madurai: 7          │
├──────────────────────────────────────────────────────────┤
│  Recent Issues (Last 7 Days)                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 2024-06-15 | Chennai | Temp | Outlier: 52.3°C    │ │
│  │ 2024-06-14 | Madurai | Rain | Missing: June 2024 │ │
│  │ 2024-06-13 | Salem   | Hum  | Out of Range: 105% │ │
│  └────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────┤
│  [View All Issues] [Generate QC Report] [Export]       │
└──────────────────────────────────────────────────────────┘
```

---

## 9. DEPLOYMENT ARCHITECTURE

### 9.1 Recommended Production Stack

```
┌─────────────────────────────────────────────────────────┐
│                  CLIENT MACHINES                        │
│  - Windows 10/11 PCs                                    │
│  - Modern browsers (Chrome, Firefox, Edge)              │
│  - Local network: 192.168.1.0/24                        │
└─────────────────────────────────────────────────────────┘
                        ↕ HTTP (Port 80)
┌─────────────────────────────────────────────────────────┐
│             NGINX (Reverse Proxy)                       │
│  - Load balancing                                       │
│  - Static file serving                                  │
│  - SSL termination (if internal CA)                     │
│  - Request logging                                      │
└─────────────────────────────────────────────────────────┘
                        ↕ Socket
┌─────────────────────────────────────────────────────────┐
│          GUNICORN (WSGI Server)                         │
│  - 4 worker processes                                   │
│  - Worker class: sync                                   │
│  - Timeout: 120 seconds                                 │
│  - Bind: unix:/tmp/wdms.sock                            │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│          FLASK APPLICATION                              │
│  - Business logic                                       │
│  - SQLAlchemy ORM                                       │
│  - Authentication/Authorization                         │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│          POSTGRESQL 14+                                 │
│  - Primary database server                              │
│  - Connection pooling (pgBouncer optional)              │
│  - Streaming replication to standby (recommended)       │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│          FILE SYSTEM                                    │
│  - Excel archive: D:\wdms\excel_archive\               │
│  - Exports: D:\wdms\exports\                            │
│  - Backups: E:\backups\wdms\  (separate drive)         │
│  - Logs: D:\wdms\logs\                                  │
└─────────────────────────────────────────────────────────┘
```


### 9.2 Hardware Requirements

**MINIMUM CONFIGURATION:**
```
Server Specifications:
- OS: Windows Server 2019/2022 or Ubuntu Server 22.04 LTS
- CPU: 4 cores (Intel Xeon or equivalent)
- RAM: 8 GB
- Storage: 
  - System: 50 GB SSD
  - Database: 100 GB SSD (with room for growth)
  - Backups: 500 GB HDD (external or NAS)
- Network: 1 Gbps LAN

Client Specifications:
- Windows 10/11
- 4 GB RAM
- Modern web browser
- Network connection to server
```

**RECOMMENDED CONFIGURATION:**
```
Server Specifications:
- OS: Windows Server 2022 or Ubuntu Server 22.04 LTS
- CPU: 8 cores
- RAM: 16 GB
- Storage:
  - System: 100 GB NVMe SSD
  - Database: 250 GB NVMe SSD
  - Backups: 1 TB external HDD or NAS
- Network: 1 Gbps LAN
- UPS: 1500 VA for power protection
- RAID: RAID 1 for database drive (mirroring)
```

### 9.3 Deployment Checklist

**PHASE 1: Pre-Deployment (Week 1-2)**
- [ ] Procure server hardware
- [ ] Install operating system
- [ ] Configure firewall rules
- [ ] Set up PostgreSQL
- [ ] Create database users and schemas
- [ ] Install Python and dependencies
- [ ] Configure Nginx
- [ ] Set up backup system

**PHASE 2: Application Setup (Week 3)**
- [ ] Deploy application code
- [ ] Run database migrations
- [ ] Create initial admin user
- [ ] Configure logging
- [ ] Set up systemd services (Linux) or Windows services
- [ ] Test application startup

**PHASE 3: Data Migration (Week 4-6)**
- [ ] Collect all Excel files
- [ ] Create station master list
- [ ] Create parameter master list
- [ ] Run migration dry-run
- [ ] Review migration report
- [ ] Perform actual migration
- [ ] Validate migrated data
- [ ] Generate data quality report

**PHASE 4: Testing (Week 7-8)**
- [ ] User acceptance testing
- [ ] Performance testing
- [ ] Security testing
- [ ] Backup/restore testing
- [ ] Failover testing
- [ ] Load testing

**PHASE 5: Training (Week 9)**
- [ ] Admin training (2 days)
- [ ] Met Officer training (2 days)
- [ ] Data Entry training (1 day)
- [ ] Read-only user orientation (0.5 days)

**PHASE 6: Go-Live (Week 10)**
- [ ] Final data synchronization
- [ ] Switch to production
- [ ] Monitor for 48 hours
- [ ] Collect user feedback
- [ ] Address immediate issues


---

## 10. RISK ASSESSMENT & MITIGATION

### 10.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| **Data loss during migration** | Medium | Critical | Dry-run mode, staging tables, backups before migration |
| **Database corruption** | Low | Critical | RAID 1, daily backups, standby server |
| **Performance degradation** | Medium | High | Proper indexing, caching, query optimization |
| **Security breach** | Low | Critical | RBAC, audit logging, network isolation, regular updates |
| **Excel file inconsistencies** | High | Medium | Robust ETL with error handling, manual review workflow |
| **User adoption resistance** | Medium | High | Comprehensive training, gradual rollout, support team |
| **Hardware failure** | Low | High | UPS, RAID, hot standby, regular backups |
| **Software bugs** | Medium | Medium | Thorough testing, staged deployment, quick rollback plan |

### 10.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| **Staff turnover** | Medium | Medium | Documentation, knowledge transfer, standard procedures |
| **Budget constraints** | Low | Medium | Use open-source stack, plan for incremental upgrades |
| **Scope creep** | Medium | Medium | Fixed MVP scope, phased enhancements |
| **Insufficient training** | Medium | High | Comprehensive training program, user manuals, video tutorials |
| **Network issues** | Low | High | Local deployment, offline fallback (read-only Excel access) |
| **Lack of technical support** | Medium | High | External consultant on retainer, vendor support for critical components |

### 10.3 Data Quality Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| **Historical data errors** | High | Medium | Quality dashboard, validation rules, manual review |
| **Duplicate entries** | Medium | Medium | Unique constraints, duplicate detection, merge tools |
| **Missing data propagation** | High | Low | Completeness tracking, gap detection, reports |
| **Incorrect data entry** | Medium | High | Input validation, range checks, confirmation dialogs |
| **Data tampering** | Low | Critical | Audit logs, role permissions, immutable audit trail |

---

## 11. FUTURE ENHANCEMENTS ROADMAP

### 11.1 Phase 2 (Year 2) - Analytics

**AI/ML Forecasting Module**
```
Capabilities:
- Rainfall prediction (1-3 months ahead)
- Temperature trend analysis
- Anomaly detection (unusual weather patterns)
- Climate change indicators

Technology:
- Python: scikit-learn, TensorFlow/PyTorch
- Time series models: ARIMA, LSTM
- Feature engineering from historical data

Database Schema Addition:
```sql
CREATE TABLE ml_models (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100),
    parameter_id INTEGER REFERENCES parameters(parameter_id),
    model_type VARCHAR(50),  -- 'ARIMA', 'LSTM', etc.
    model_file_path VARCHAR(255),
    training_data_range DATERANGE,
    accuracy_metrics JSONB,
    created_at TIMESTAMP,
    is_active BOOLEAN
);

CREATE TABLE predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ml_models(model_id),
    station_id INTEGER REFERENCES stations(station_id),
    parameter_id INTEGER REFERENCES parameters(parameter_id),
    prediction_date DATE,
    predicted_value DECIMAL(12, 4),
    confidence_interval JSONB,  -- {lower: x, upper: y}
    actual_value DECIMAL(12, 4),  -- Filled when data available
    prediction_error DECIMAL(12, 4),
    created_at TIMESTAMP
);
```


### 11.2 Phase 3 (Year 3) - Integration

**Real-Time Data Ingestion**
```
Capabilities:
- Automatic data import from AWS (Automatic Weather Stations)
- API integration with other IMD systems
- Real-time dashboard updates
- Alert system for extreme values

Technology:
- Message queue: RabbitMQ or Redis Pub/Sub
- WebSockets for real-time updates
- RESTful API for external systems

Architecture Addition:
┌─────────────────────────────────────────┐
│  AWS Stations (Automatic Weather)       │
│  - Send data every 15 minutes           │
│  - FTP, HTTP POST, or MQTT              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Data Ingestion Service                 │
│  - Validate incoming data               │
│  - Queue for processing                 │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Processing Queue (RabbitMQ)            │
│  - Ensures no data loss                 │
│  - Retry mechanism                      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  WDMS Database                          │
│  - Insert observations                  │
│  - Update statistics                    │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  WebSocket Server                       │
│  - Notify connected clients             │
│  - Update dashboards in real-time       │
└─────────────────────────────────────────┘
```

### 11.3 Phase 4 (Year 4-5) - Expansion

**Multi-Region Support**
```
Expand to all IMD Regional Centres:
- Chennai (existing)
- Mumbai
- Kolkata
- New Delhi
- Pune
- Nagpur

Architecture Changes:
- Multi-tenant database design
- Region-based data partitioning
- Federated search across regions
- Central reporting dashboard
```

**Mobile Application**
```
Features:
- View latest observations
- Search historical data
- Receive alerts
- Submit field observations (with GPS)

Technology:
- React Native (cross-platform)
- Offline-first architecture
- Sync when connected
```

### 11.4 Phase 5 (Year 6+) - Advanced Features

**Climate Research Tools**
```
- Statistical analysis tools
- Climate indices calculation (SPI, PDI, etc.)
- Extreme event analysis
- Climate zone mapping
- Publication-ready charts and tables
```

**Public Data Portal**
```
- Separate public-facing website
- Limited data access (with embargo periods)
- API for researchers
- Data request workflow
- DOI assignment for datasets
```


---

## 12. COST-BENEFIT ANALYSIS

### 12.1 Development Costs

| Item | Estimated Cost (INR) |
|------|---------------------|
| Server Hardware | ₹2,00,000 |
| Windows Server License (if used) | ₹50,000 |
| PostgreSQL (Open Source) | ₹0 |
| Development (in-house or outsourced) | ₹5,00,000 - ₹10,00,000 |
| Testing & QA | ₹1,00,000 |
| Training | ₹50,000 |
| Documentation | ₹50,000 |
| **Total Initial Investment** | **₹9,00,000 - ₹14,00,000** |

### 12.2 Operational Costs (Annual)

| Item | Estimated Cost (INR/year) |
|------|---------------------------|
| Electricity | ₹30,000 |
| Internet/Network | ₹20,000 |
| Backup Storage | ₹10,000 |
| Maintenance | ₹1,00,000 |
| Support (if external) | ₹50,000 |
| **Total Annual Cost** | **₹2,10,000** |

### 12.3 Benefits

**Quantifiable Benefits:**
```
Time Savings:
- Current: 2-5 minutes per query × 50 queries/day × 20 officers = 1,667 hours/month
- New System: 0.5 minutes per query = 333 hours/month
- Time Saved: 1,334 hours/month ≈ 167 person-days/month

Assuming ₹500/hour officer time:
Annual Savings = 1,334 hours × 12 months × ₹500 = ₹80,04,000

ROI = (₹80,04,000 - ₹2,10,000) / ₹14,00,000 = 556% in Year 1
```

**Non-Quantifiable Benefits:**
- Improved data quality and reliability
- Enhanced decision-making with better analytics
- Reduced risk of data loss
- Better compliance with government data standards
- Foundation for future AI/ML initiatives
- Improved inter-departmental collaboration
- Enhanced reputation of IMD Chennai
- Better service to public and researchers

### 12.4 Break-Even Analysis

```
Initial Investment: ₹14,00,000 (worst case)
Annual Savings: ₹77,94,000 (time + reduced errors)
Break-Even: < 1 month ✅

Conclusion: Highly favorable ROI
```

---

## 13. SUCCESS METRICS

### 13.1 Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| System Uptime | 99.5% | Monthly monitoring |
| Query Response Time | < 100ms for 95% of queries | Application logs |
| Data Migration Success Rate | > 98% | Migration reports |
| Database Growth Rate | < 10 GB/year | Database size monitoring |
| Backup Success Rate | 100% | Backup logs |
| Security Incidents | 0 | Security audit logs |

### 13.2 User Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| User Adoption Rate | > 90% within 3 months | User login tracking |
| User Satisfaction | > 4.0/5.0 | Quarterly surveys |
| Training Completion | 100% | Training records |
| Support Tickets | < 5/week after 3 months | Ticket system |
| Data Entry Speed | 3× faster than Excel | Time tracking |

### 13.3 Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to Retrieve Data | < 1 minute | User surveys |
| Report Generation Time | < 5 minutes | System logs |
| Data Quality Score | > 95% | Quality dashboard |
| Cost Savings | > ₹50 lakhs/year | Financial analysis |
| User Productivity Gain | > 30% | Before/after study |


---

## 14. CRITICAL RECOMMENDATIONS

### Priority 1: MUST HAVE (Before Go-Live)

1. **✅ Implement Staging Tables for Migration**
   - Never directly import to production tables
   - Allow manual review before final commit
   - Rollback capability essential

2. **✅ Set Up Automated Backups with Verification**
   - Daily PostgreSQL dumps
   - Test restore every month
   - Store on separate physical drive

3. **✅ Implement Comprehensive Error Handling**
   - Try-catch blocks in all critical functions
   - User-friendly error messages
   - Detailed logging for debugging

4. **✅ Add Input Validation at Multiple Levels**
   - Client-side (JavaScript)
   - Server-side (Flask)
   - Database-level (constraints, triggers)

5. **✅ Create Admin Dashboard for Monitoring**
   - System health check
   - Database statistics
   - User activity
   - Error logs

### Priority 2: SHOULD HAVE (Within 3 Months)

6. **⚡ Implement Caching Layer**
   - Redis for session storage
   - Query result caching for dashboard
   - Significant performance improvement

7. **⚡ Add Rate Limiting**
   - Prevent brute force attacks
   - Limit API calls per user
   - Protect against DoS

8. **⚡ Create Materialized Views for Reports**
   - Pre-calculate common aggregations
   - Refresh daily
   - Dramatically faster report generation

9. **⚡ Implement Background Jobs**
   - Async report generation
   - Email notifications
   - Celery or RQ task queue

10. **⚡ Add Data Export Optimization**
    - Streaming responses for large exports
    - Compression for downloads
    - Progress indicators

### Priority 3: NICE TO HAVE (Within 1 Year)

11. **📊 Advanced Visualizations**
    - Interactive maps
    - 3D charts
    - Animated time series

12. **📊 Automated Quality Reports**
    - Weekly email summaries
    - Monthly quality scorecards
    - Trend analysis

13. **📊 Mobile-Responsive Design**
    - Optimize for tablets
    - Touch-friendly interfaces
    - Offline capability

14. **📊 API Development**
    - RESTful API for external systems
    - API key management
    - Usage quotas

15. **📊 Advanced Search**
    - Natural language queries
    - Fuzzy matching
    - Saved search filters


---

## 15. ARCHITECTURAL DECISION RECORDS (ADRs)

### ADR-001: Use PostgreSQL over MySQL

**Status**: Accepted

**Context**: Need to choose relational database

**Decision**: PostgreSQL 14+

**Rationale**:
- Better support for complex queries and JSON data
- Superior full-text search capabilities
- More robust transaction handling
- Excellent support for time-series data
- Strong reputation in government/enterprise
- Better PostGIS integration for future geospatial features

**Consequences**:
- ✅ Better performance for complex analytics
- ✅ More flexible schema evolution
- ❌ Slightly steeper learning curve than MySQL
- ❌ Fewer GUI tools compared to MySQL

---

### ADR-002: Flask over Django

**Status**: Accepted

**Context**: Need to choose Python web framework

**Decision**: Flask 2.3+

**Rationale**:
- Lightweight and flexible
- Easier to understand for maintenance
- Better control over application structure
- Sufficient for internal application
- Faster development for simple CRUD operations
- Lower resource requirements

**Consequences**:
- ✅ Faster development
- ✅ Simpler deployment
- ✅ Less resource intensive
- ❌ No built-in admin panel (need to build)
- ❌ Need to choose own ORM (SQLAlchemy)

---

### ADR-003: Server-Side Rendering over SPA

**Status**: Accepted

**Context**: Choose frontend architecture

**Decision**: Server-side rendering with Jinja2

**Rationale**:
- Internal application, no need for complex frontend
- Better SEO (if needed for intranet)
- Simpler security model
- Works without JavaScript
- Faster initial page load
- Easier to maintain for small team

**Consequences**:
- ✅ Simpler architecture
- ✅ Better for low-bandwidth networks
- ✅ Easier debugging
- ❌ Less interactive user experience
- ❌ More server load for page rendering
- ⚠️ Can enhance with AJAX where needed

---

### ADR-004: Monthly Granularity over Daily

**Status**: Accepted

**Context**: Choose data granularity level

**Decision**: Store monthly aggregated data

**Rationale**:
- Current data is already monthly in Excel
- Meteorological reports typically monthly/yearly
- Significantly reduces database size
- Matches user mental model
- Historical data is monthly

**Consequences**:
- ✅ Smaller database size
- ✅ Faster queries
- ✅ Easier migration from Excel
- ❌ Cannot answer daily questions
- ⚠️ Can be extended to daily if needed (separate table)

---

### ADR-005: Local Deployment over Cloud

**Status**: Accepted

**Context**: Choose deployment model

**Decision**: On-premises local server

**Rationale**:
- Government data security requirements
- No internet dependency
- Faster access on local network
- Lower operational costs
- Full control over infrastructure
- Compliance with IMD policies

**Consequences**:
- ✅ Better security
- ✅ No recurring cloud costs
- ✅ Faster local access
- ❌ Need to manage own hardware
- ❌ No automatic scaling
- ❌ Backup responsibility on department


---

## 16. FINAL RECOMMENDATIONS

### 16.1 Architecture Approval

**✅ APPROVED WITH MODIFICATIONS**

The proposed architecture is fundamentally sound and suitable for a 10+ year production system. However, the following modifications are MANDATORY:

1. **Add Staging Tables** - Non-negotiable for data migration safety
2. **Implement Backup Verification** - Critical for disaster recovery
3. **Add Caching Layer** - Important for performance longevity
4. **Database Partitioning Strategy** - Plan now, implement when needed
5. **Comprehensive Error Handling** - Essential for production stability

### 16.2 Implementation Approach

**RECOMMENDED: Phased Implementation**

**Phase 0: Foundation (Week 1-2)**
- Set up development environment
- Create database schema
- Implement core models
- Set up version control (Git)

**Phase 1: MVP (Week 3-6)**
- Authentication system
- Basic data entry
- Simple search
- Manual data migration

**Phase 2: Migration Tool (Week 7-10)**
- Excel parser
- ETL pipeline
- Data validation
- Quality checks

**Phase 3: Reporting (Week 11-14)**
- Report templates
- PDF generation
- Excel export
- Charts and visualizations

**Phase 4: Admin Features (Week 15-16)**
- User management
- System monitoring
- Backup tools
- Audit logs

**Phase 5: Testing & Deployment (Week 17-20)**
- User acceptance testing
- Performance testing
- Security audit
- Training
- Go-live

### 16.3 Team Requirements

**Minimum Team:**
- 1 × Backend Developer (Python/Flask/PostgreSQL)
- 1 × Frontend Developer (HTML/CSS/JavaScript)
- 1 × Database Administrator (part-time)
- 1 × System Administrator (for deployment)
- 1 × QA Tester
- 1 × Project Manager / Technical Lead

**OR**

- 1-2 Full-stack Developers (if experienced)
- 1 × Database/System Administrator (part-time)
- 1 × Project Manager

### 16.4 Technology Stack Final Approval

| Component | Technology | Status |
|-----------|-----------|--------|
| Backend Language | Python 3.9+ | ✅ Approved |
| Web Framework | Flask 2.3+ | ✅ Approved |
| Database | PostgreSQL 14+ | ✅ Approved |
| ORM | SQLAlchemy 2.0+ | ✅ Approved |
| Frontend | Bootstrap 5 | ✅ Approved |
| Charts | Chart.js | ✅ Approved |
| Tables | DataTables | ✅ Approved |
| WSGI Server | Gunicorn | ✅ Approved |
| Reverse Proxy | Nginx | ✅ Approved |
| Caching | Redis | ⚠️ Add in Phase 2 |
| Task Queue | Celery/RQ | ⚠️ Add in Phase 2 |

### 16.5 Go/No-Go Criteria

**PROCEED WITH IMPLEMENTATION IF:**
- ✅ Budget approved (₹9-14 lakhs initial + ₹2 lakhs annual)
- ✅ Server hardware procured or ordered
- ✅ Development team identified
- ✅ Project timeline acceptable (5-6 months to go-live)
- ✅ All stakeholders on board
- ✅ Excel files available for migration
- ✅ Station and parameter master lists prepared

**DO NOT PROCEED IF:**
- ❌ No dedicated server hardware
- ❌ Insufficient budget
- ❌ No technical team available
- ❌ Stakeholders not committed
- ❌ Critical requirements unclear


---

## 17. CONCLUSION

### Executive Summary for Decision Makers

**Project Viability**: ✅ **HIGHLY VIABLE**

**Technical Feasibility**: ✅ **PROVEN TECHNOLOGIES**

**Financial Viability**: ✅ **ROI > 500% in Year 1**

**Risk Level**: ⚠️ **MODERATE** (manageable with proper planning)

**Recommendation**: **PROCEED WITH IMPLEMENTATION**

---

### Key Strengths of Proposed Solution

1. **Right-Sized Technology Stack**
   - Not over-engineered
   - Not under-powered
   - Perfect for 10+ year lifespan

2. **Clear Data Migration Path**
   - Handles Excel inconsistencies
   - Validates during import
   - Preserves data lineage

3. **User-Centric Design**
   - Significantly faster than current workflow
   - Intuitive interface
   - Comprehensive training plan

4. **Future-Proof Architecture**
   - Can scale to all-India deployment
   - Ready for AI/ML integration
   - Supports real-time data ingestion

5. **Cost-Effective**
   - Breaks even in < 1 month
   - Low operational costs
   - High ROI

---

### Critical Success Factors

1. **Data Quality During Migration** - Most important
2. **User Training and Adoption** - Second most important
3. **Performance Optimization** - Important for longevity
4. **Backup and Disaster Recovery** - Critical for government data
5. **Security and Access Control** - Non-negotiable

---

### Next Steps

1. **Immediate (This Week)**
   - Obtain stakeholder approval
   - Secure budget
   - Procure server hardware

2. **Short Term (This Month)**
   - Finalize development team
   - Set up development environment
   - Create detailed project plan
   - Collect all Excel files

3. **Medium Term (Next 3 Months)**
   - Develop MVP
   - Perform initial data migration
   - Begin user testing

4. **Long Term (6 Months)**
   - Complete development
   - Full data migration
   - Training
   - Go-live

---

## APPROVAL SIGNATURES

**Prepared By:**
Principal Software Architect  
Date: ________________

**Reviewed By:**
Senior Meteorological Officer  
Date: ________________

**Approved By:**
Director, Regional Meteorological Centre, Chennai  
Date: ________________

---

**Document Status**: FINAL DRAFT v1.0  
**Confidentiality**: INTERNAL USE ONLY  
**Distribution**: IMD Chennai Leadership, Project Team  

---

*This architecture review document should be revisited and updated at key project milestones and annually after deployment.*

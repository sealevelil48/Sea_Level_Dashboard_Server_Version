-- ============================================
-- PERFORMANCE INDEXES FOR LARGE DATE RANGES
-- ============================================

-- Index for Monitors_info2 table (main sea level data)
CREATE INDEX IF NOT EXISTS idx_monitors_datetime 
ON "Monitors_info2" ("Tab_DateTime");

CREATE INDEX IF NOT EXISTS idx_monitors_tag 
ON "Monitors_info2" ("Tab_TabularTag");

-- Composite index for common query pattern (MOST IMPORTANT!)
CREATE INDEX IF NOT EXISTS idx_monitors_station_date 
ON "Monitors_info2" ("Tab_TabularTag", "Tab_DateTime");

-- Index for date-only queries (for daily aggregations)
CREATE INDEX IF NOT EXISTS idx_monitors_date_only 
ON "Monitors_info2" (DATE("Tab_DateTime"));

-- Index for Locations table
CREATE INDEX IF NOT EXISTS idx_locations_station 
ON "Locations" ("Station");

CREATE INDEX IF NOT EXISTS idx_locations_tag 
ON "Locations" ("Tab_TabularTag");

-- Index for SeaTides table
CREATE INDEX IF NOT EXISTS idx_tides_date 
ON "SeaTides" ("Date");

CREATE INDEX IF NOT EXISTS idx_tides_station_date 
ON "SeaTides" ("Station", "Date");

-- Analyze tables to update statistics
ANALYZE "Monitors_info2";
ANALYZE "Locations";
ANALYZE "SeaTides";
-- Fix database permissions for SeaLevel user
-- Connect to your database as a superuser (postgres) and run these commands

-- Connect to the correct database
\c "Test2-SeaLevels_Restored"

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO "SeaLevel";

-- Grant select permissions on required tables
GRANT SELECT ON "Locations" TO "SeaLevel";
GRANT SELECT ON "Monitors_info2" TO "SeaLevel";

-- Grant all privileges on all tables in public schema (recommended)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "SeaLevel";

-- Grant privileges on sequences (for auto-increment columns)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "SeaLevel";

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "SeaLevel";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "SeaLevel";
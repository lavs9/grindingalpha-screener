-- Database initialization script for screener_db
-- This script runs automatically when PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges (PostgreSQL automatically creates the database and user from env vars)
-- Additional configuration can be added here as needed

-- Log initialization
SELECT 'Database initialized successfully' as message;

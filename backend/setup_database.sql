-- Setup script for PostgreSQL database
-- Run this with: psql -U postgres -f setup_database.sql

-- Create database
CREATE DATABASE escrow_dev;

-- Create user
CREATE USER escrow_user WITH PASSWORD 'dev_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE escrow_dev TO escrow_user;

-- Allow user to create databases (for tests)
ALTER USER escrow_user CREATEDB;

-- Connect to the database and grant schema privileges
\c escrow_dev
GRANT ALL ON SCHEMA public TO escrow_user;

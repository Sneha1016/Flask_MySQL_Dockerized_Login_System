-- init.sql
-- This SQL script runs automatically when MySQL container starts
-- It creates the users table in the database

-- Use the flask_auth_db database
-- This database is created automatically by docker-compose.yml (MYSQL_DATABASE)
USE flask_auth_db;

-- Create users table if it doesn't exist
-- This table stores all user authentication information
CREATE TABLE IF NOT EXISTS users (
    -- id: Primary key, auto-incremented for each new user
    -- INT: Integer data type
    -- AUTO_INCREMENT: Automatically generates unique ID for each new row
    -- PRIMARY KEY: Uniquely identifies each record
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- username: Stores user's username
    -- VARCHAR(80): Variable character string, max 80 characters
    -- UNIQUE: Ensures no two users can have same username
    -- NOT NULL: Field cannot be empty
    username VARCHAR(80) UNIQUE NOT NULL,
    
    -- email: Stores user's email address
    -- VARCHAR(120): Variable character string, max 120 characters
    -- UNIQUE: Ensures no two users can have same email
    -- NOT NULL: Field cannot be empty
    email VARCHAR(120) UNIQUE NOT NULL,
    
    -- password: Stores hashed password (NOT plain text)
    -- VARCHAR(255): Large enough to store hashed password
    -- NOT NULL: Field cannot be empty
    password VARCHAR(255) NOT NULL,
    
    -- created_at: Timestamp of when user registered
    -- TIMESTAMP: Stores date and time
    -- DEFAULT CURRENT_TIMESTAMP: Automatically sets to current time when record created
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on email for faster login queries
-- INDEX: Speeds up searches on email field
-- When user logs in with email, database can find record quickly
CREATE INDEX idx_email ON users(email);

-- Create an index on username for faster queries
-- Speeds up searches when looking up users by username
CREATE INDEX idx_username ON users(username);
#!/bin/bash

# Load environment variables from .env
export $(grep -v '^#' .env | xargs)
# Define the database connection parameters
DB_HOST="journaldb.electricity.works"
DB_NAME="journaldb"
DB_USER="persister"

# Delete the existing database
echo "Deleting database $DB_NAME..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"

# Recreate the database
echo "Creating database $DB_NAME..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

# Run Alembic migration
echo "Running Alembic migrations..."
alembic upgrade head


# Generate the SQL command to create the view if it does not exist
SQL_COMMAND="CREATE OR REPLACE VIEW msg_pretty AS 
SELECT 
    payload, 
    to_timestamp(message_persisted_ms / 1000) AT TIME ZONE 'America/New_York' AS message_persisted, 
    CASE 
        WHEN message_created_ms IS NOT NULL THEN to_timestamp(message_created_ms / 1000) AT TIME ZONE 'America/New_York' 
        ELSE NULL 
    END AS message_created 
FROM messages;"

# Execute the SQL command
export PGPASSWORD="$GWP_DBPASS"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "$SQL_COMMAND"

echo "View 'msg_pretty' created or replaced successfully."

CREATE VIEW readings_pretty AS
SELECT
    dc.name AS name,
    r.value AS value,
    dc.telemetry_name AS telemetry_name,
    to_timestamp(time_ms / 1000.0) AT TIME ZONE 'America/New_York' AS time
FROM
    readings r
JOIN
    data_channels dc
ON
    r.data_channel_id = dc.id;



SELECT * FROM preadings WHERE name LIKE '%buffer%' LIMIT 5;


CREATE OR REPLACE VIEW msg_pretty AS
SELECT
    payload, from_alias, type_name,
    to_timestamp(message_persisted_ms / 1000.0) AT TIME ZONE 'America/New_York' AS message_persisted,
    CASE
        WHEN message_created_ms IS NOT NULL THEN to_timestamp(message_created_ms / 1000.0) AT TIME ZONE 'America/New_York'
        ELSE NULL
    END AS message_created
FROM messages;




SELECT COUNT(*) from messages;

SELECT COUNT(*) FROM messages WHERE type_name = 'power.watts';

SELECT from_alias, type_name, message_created FROM msg_pretty WHERE type_name LIKE '%status%' LIMIT 5;

SELECT pg_size_pretty(pg_database_size('journaldb')) AS size;
SELECT * FROM msg_pretty WHERE type_name LIKE '%param%';

SELECT message_id, from_alias, type_name, message_persisted_ms FROM messages WHERE type_name LIKE '%param%';

DELETE FROM messages WHERE message_id = 'bf06df07-36a5-4e54-ae64-37dea6041ea8';

SELECT MIN(time) AS earliest, MAX(time) AS latest FROM  readings_pretty;
SELECT MIN(message_created) AS earliest, MAX(message_created) AS latest FROM  msg_pretty;

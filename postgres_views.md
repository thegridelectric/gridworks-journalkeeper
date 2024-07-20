CREATE VIEW preadings AS
SELECT
    dc.name AS name,
    r.value AS value,
    dc.telemetry_name AS telemetry_name,
    to_char(
        to_timestamp(r.time_ms / 1000.0),
        'YYYY-MM-DD HH24:MI:SS.MS'
    ) AS time
FROM
    readings r
JOIN
    data_channels dc
ON
    r.data_channel_id = dc.id;





SELECT * FROM preadings WHERE name LIKE '%buffer%' LIMIT 5;
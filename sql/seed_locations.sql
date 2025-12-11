-- Seed some Oregon locations for AQI tracking

INSERT INTO locations (name, latitude, longitude) VALUES
    ('Portland', 45.5152, -122.6784),
    ('Eugene', 44.0521, -123.0868),
    ('Salem', 44.9429, -123.0351),
    ('Bend', 44.0582, -121.3153),
    ('Medford', 42.3265, -122.8756)
ON CONFLICT DO NOTHING;

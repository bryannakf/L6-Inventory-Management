-- Run this using a SQLite browser or via Python script
CREATE TABLE IF NOT EXISTS datacenter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    capacity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    datacenter_id INTEGER NOT NULL,
    FOREIGN KEY(datacenter_id) REFERENCES datacenter(id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS actionsAudit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- db.execute("""
-- CREATE TABLE IF NOT EXISTS actionsAudit (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     username TEXT NOT NULL,
--     action TEXT NOT NULL,
--     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
-- )
-- """)

-- conn.commit()
-- conn.close()

-- Datacenters
INSERT INTO datacenter (location, capacity) VALUES 
('New York', 1000),
('London', 850),
('Tokyo', 900),
('Berlin', 750),
('Sydney', 950),
('Paris', 800),
('Toronto', 920),
('Dubai', 870),
('San Francisco', 980),
('Singapore', 990);

-- Inventory
INSERT INTO inventory (item_name, quantity, datacenter_id) VALUES 
('Server A', 10, 1),
('Server B', 15, 2),
('Router X', 20, 3),
('Switch Z', 5, 4),
('Storage Y', 8, 5),
('Server C', 12, 6),
('UPS Unit', 7, 7),
('Cooling Fan', 18, 8),
('Firewall Device', 6, 9),
('Load Balancer', 11, 10);


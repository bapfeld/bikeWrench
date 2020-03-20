-- Riders are top level
CREATE TABLE riders (
    name       TEXT PRIMARY KEY,
    max_speed  REAL,
    avg_speed  REAL,
    total_dist REAL,
    units      TEXT
);

-- Bikes belong to riders
CREATE TABLE bikes (
    id          TEXT PRIMARY KEY,
    name        TEXT,
    color       TEXT,
    purchased   DATE,
    price       REAL,
    total_mi    REAL,
    total_elev  REAL
);

-- Rides record data about a bike ride
CREATE TABLE rides (
    id           INTEGER PRIMARY KEY,
    bike         TEXT NOT NULL REFERENCES bike(id),
    distance     INTEGER,
    name         TEXT,
    date         DATE,
    moving_time  INTEGER,
    elapsed_time INTEGER,
    elev         REAL,
    type         TEXT,
    avg_speed    REAL,
    max_speed    REAL,
    calories     REAL,
    rider        TEXT NOT NULL REFERENCES rider(name)
);

-- Parts belong to bikes
CREATE TABLE parts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    type         TEXT,
    purchased    DATE,
    brand        TEXT,
    price        REAL,
    weight       REAL,
    size         TEXT,
    model        TEXT,
    bike         TEXT NOT NULL REFERENCES bikes(name),
    inuse        TEXT
);

-- Maintenance tasks record things that happen to parts
CREATE TABLE maintenance (
    id           INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    part         INTEGER NOT NULL REFERENCES parts(id),
    work         TEXT,
    date         DATE
);

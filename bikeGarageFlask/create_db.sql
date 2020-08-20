-- Riders are top level
CREATE TABLE riders (
    name       TEXT PRIMARY KEY,
    units      TEXT,
    r_tkn      TEXT,
    tkn_exp    DATETIME
);

-- Bikes belong to riders
CREATE TABLE bikes (
    bike_id     TEXT PRIMARY KEY,
    name        TEXT,
    color       TEXT,
    purchased   DATE,
    price       REAL,
    mfg         TEXT
);

-- Rides record data about a bike ride
CREATE TABLE rides (
    ride_id      INTEGER PRIMARY KEY,
    bike         TEXT NOT NULL REFERENCES bikes(bike_id),
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
    part_id      INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    type         TEXT,
    purchased    DATE,
    brand        TEXT,
    price        REAL,
    weight       REAL,
    size         TEXT,
    model        TEXT,
    bike         TEXT NOT NULL REFERENCES bikes(bike_id),
    inuse        TEXT
);

-- Maintenance tasks record things that happen to parts
CREATE TABLE maintenance (
    maint_id     INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    part         INTEGER NOT NULL REFERENCES parts(part_id),
    work         TEXT,
    date         DATE
);

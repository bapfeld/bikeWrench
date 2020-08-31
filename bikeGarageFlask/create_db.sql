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
    calories     REAL
);

-- Parts belong to bikes
CREATE TABLE parts (
    part_id      INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    type         TEXT,
    added        DATE,
    brand        TEXT,
    price        REAL,
    weight       REAL,
    size         TEXT,
    model        TEXT,
    bike         TEXT NOT NULL REFERENCES bikes(bike_id),
    retired      DATE
);

-- Record retired parts separately
CREATE TABLE retired_parts (
    part_id      INTEGER REFERENCES parts(part_id),
    type         TEXT,
    added        DATE,
    brand        TEXT,
    price        REAL,
    weight       REAL,
    size         TEXT,
    model        TEXT,
    bike         TEXT NOT NULL REFERENCES bikes(bike_id),
    retired      DATE,
    dist         REAL,
    elev         REAL
);

-- Maintenance tasks record things that happen to parts
CREATE TABLE maintenance (
    maint_id     INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    part         INTEGER NOT NULL REFERENCES parts(part_id),
    work         TEXT,
    date         DATE
);

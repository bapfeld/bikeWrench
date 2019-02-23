-- Riders are top level
create table riders (
    name       text primary key,
    max_speed  real,
    avg_speed  real,
    total_dist real,
    units      text
);

-- Bikes belong to riders
create table bikes (
    id          text primary key,
    name        text,
    color       text,
    purchased   date,
    price       real,
    total_mi    real,
    total_elev  real
);

-- Rides record data about a bike ride
create table rides (
    id           integer primary key,
    bike         text not null references bike(id),
    distance     integer,
    name         text,
    date         date,
    moving_time  integer,
    elapsed_time integer,
    elev         real,
    type         text,
    avg_speed    real,
    max_speed    real,
    calories     real,
    rider        text not null references rider(name)
);

-- Parts belong to bikes
create table parts (
    id           integer primary key autoincrement not null,
    type         text,
    purchased    date,
    brand        text,
    price        real,
    weight       real,
    size         text,
    model        text,
    bike         text not null references bikes(name),
    inuse        text
);

-- Maintenance tasks record things that happen to parts
create table maintenance (
    id           integer primary key autoincrement not null,
    part         integer not null references parts(id),
    work         text,
    date         date
);

-- Schema for to-do application examples.

-- Riders are top level
create table riders (
    name       text primary key,
    dob        date,
    weight     integer,
    fthr       integer,
    max_speed  real,
    avg_speed  real
);

-- Bikes belong to riders
create table bikes (
    id          text primary key,
    name        text,
    color       text,
    purchased   date,
    price       real,
    rider       text not null references rider(name)
);

-- Rides record data about a bike ride
create table ride (
    id           integer primary key,
    bike         text not null references bike(id),
    distance     integer,
    name         text,
    moving_time  integer,
    elapsed_time integer,
    elev         real,
    type         text,
    avg_speed    real,
    max_speed    real,
    calories     real
);

-- Parts belong to bikes
create table parts (
    id           integer primary key autoincrement not null,
    type         text,
    purchased    date,
    distance     integer,
    last_service date,
    brand        text,
    price        real,
    weight       real,
    size         text,
    model        text,
    bike         text not null references bikes(id)
);

-- Maintenance tasks record things that happen to parts
create table maintenance (
    id           integer primary key autoincrement not null,
    part         text not null references parts(id),
    work         text,
    date         date
);

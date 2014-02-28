-- tested with postgresql
-- you can add a unique sequence id to the table if you want

drop table linksdb;

create table linksdb (
    urlname        varchar(256) not null,
    parentname     varchar(256),
    baseref        varchar(256),
    valid          int,
    result         varchar(256),
    warning        varchar(512),
    info           varchar(512),
    url            varchar(256),
    line           int,
    col            int,
    name           varchar(256),
    checktime      int,
    dltime         int,
    size           int,
    cached         int,
    level          int not null,
    modified       varchar(256)
);

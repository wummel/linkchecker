-- tested with postgresql
-- you can add a unique sequence id to the table if you want

drop table linksdb;

create table linksdb (
    urlname        varchar(256) not null,
    recursionlevel int not null,
    parentname     varchar(256),
    baseref        varchar(256),
    errorstring    varchar(256),
    validstring    varchar(256),
    warningstring  varchar(512),
    infostring     varchar(512),
    valid          int,
    url            varchar(256),
    line           int,
    col            int,
    name           varchar(256),
    checktime      int,
    dltime         int,
    dlsize         int,
    cached         int
);

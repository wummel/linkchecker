-- tested with postgresql

drop table linksdb;

create table linksdb (
    urlname        varchar(50) not null,
    recursionlevel int not null,
    parentname     varchar(50),
    baseref        varchar(50),
    errorstring    varchar(50),
    validstring    varchar(50),
    warningstring  varchar(50),
    infostring     varchar(150),
    valid          int,
    url            varchar(50),
    line           int,
    colum          int,
    name           varchar(50),
    checktime      int,
    dltime         int,
    dlsize         int,
    cached         int
);

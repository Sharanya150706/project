create database billnova;
use billnova;
create table admin(
admin_id int primary key auto_increment,
username varchar(50) not null unique,
password varchar(255) not null
);
show tables;
select * from admin;
insert into admin(username, password)
values('admin','admin123');
select * from admin;
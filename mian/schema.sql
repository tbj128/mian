create table accounts (
  id integer primary key autoincrement,
  user_email text not null,
  password_hash text not null,
  salt text not null
);
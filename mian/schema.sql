create table if not exists accounts (
  id integer primary key autoincrement,
  user_email text not null,
  password_hash text not null,
  salt text not null
);

create table if not exists reset (
  id integer,
  secret text not null,
  expiry integer not null
);

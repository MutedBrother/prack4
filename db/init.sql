CREATE TABLE phones (
  id SERIAL PRIMARY KEY,
  phonenum VARCHAR(100) NOT NULL
);

CREATE TABLE emails (
  id SERIAL PRIMARY KEY,
  email VARCHAR(100) NOT NULL
);

INSERT INTO phones(phonenum) VALUES ('+7904567390');
INSERT INTO phones(phonenum) VALUES ('9876543210');
INSERT INTO emails(email) VALUES ('test1@example.com');
INSERT INTO emails(email) VALUES ('test2@example.com');

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'kali';
SELECT pg_create_physical_replication_slot('replication_slot');

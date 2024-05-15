CREATE TABLE phonenums (
  id SERIAL PRIMARY KEY,
  phonenum VARCHAR(100) NOT NULL
);

CREATE TABLE emails (
  id SERIAL PRIMARY KEY,
  email VARCHAR(100) NOT NULL
);

INSERT INTO phonenums(phonenum) VALUES ('+7904567390');
INSERT INTO phonenums(phonenum) VALUES ('9876543210');
INSERT INTO emails(email) VALUES ('test1@example.com');
INSERT INTO emails(email) VALUES ('test2@example.com');

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'repl_pass';
SELECT pg_create_physical_replication_slot('replication_slot');

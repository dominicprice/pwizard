-- table with manual primary key
-- generate insert only (no update, save, upsert, delete)
CREATE TABLE a_manual_table (
  a_text VARCHAR(255)
);

-- table with sequence
CREATE TABLE a_sequence (
  a_seq INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT
);

CREATE TABLE a_sequence_multi (
  a_seq INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  a_text VARCHAR(255)
);

-- table with primary key
CREATE TABLE a_primary (
  a_key INTEGER NOT NULL PRIMARY KEY
);

CREATE TABLE a_primary_multi (
  a_key INTEGER NOT NULL PRIMARY KEY,
  a_text VARCHAR(255)
);

-- table with composite primary key
CREATE TABLE a_primary_composite (
  a_key1 INTEGER NOT NULL,
  a_key2 INTEGER NOT NULL,
  PRIMARY KEY (a_key1, a_key2)
);

-- table with foreign key
CREATE TABLE a_foreign_key (
  a_key INTEGER REFERENCES a_primary (a_key)
);

-- table with composite foreign key
CREATE TABLE a_foreign_key_composite (
  a_key1 INTEGER,
  a_key2 INTEGER,
  FOREIGN KEY (a_key1, a_key2) REFERENCES a_primary_composite (a_key1, a_key2)
);

-- table with index
CREATE TABLE a_index (
  a_key INTEGER
);

CREATE INDEX a_index_idx ON a_index (a_key);

-- table with composite index
CREATE TABLE a_index_composite (
  a_key1 INTEGER,
  a_key2 INTEGER
);

CREATE INDEX a_index_composite_idx ON a_index_composite (a_key1, a_key2);

-- table with unique index
CREATE TABLE a_unique_index (
  a_key INTEGER UNIQUE
);

-- table with composite unique index
CREATE TABLE a_unique_index_composite (
  a_key1 INTEGER,
  a_key2 INTEGER,
  UNIQUE (a_key1, a_key2)
);

/*
bigint
blob
bool
boolean
date
datetime
decimal
float
int
integer
numeric
real
smallint
text
time
varchar
*/

-- table with all field types and all nullable field types
CREATE TABLE a_bit_of_everything (
  a_bigint BIGINT NOT NULL,
  a_bigint_nullable BIGINT,
  a_blob BLOB NOT NULL,
  a_blob_nullable BLOB,
  a_bool BOOL NOT NULL,
  a_bool_nullable BOOL,
  a_boolean BOOLEAN NOT NULL,
  a_boolean_nullable BOOLEAN,
  a_date DATE NOT NULL,
  a_date_nullable DATE,
  a_datetime DATETIME NOT NULL,
  a_datetime_nullable DATETIME,
  a_decimal DECIMAL NOT NULL,
  a_decimal_nullable DECIMAL,
  a_float FLOAT NOT NULL,
  a_float_nullable FLOAT,
  a_int INT NOT NULL,
  a_int_nullable INT,
  a_integer INTEGER NOT NULL,
  a_integer_nullable INTEGER,
  a_numeric NUMERIC NOT NULL,
  a_numeric_nullable NUMERIC,
  a_real REAL NOT NULL,
  a_real_nullable REAL,
  a_smallint SMALLINT NOT NULL,
  a_smallint_nullable SMALLINT,
  a_text TEXT NOT NULL,
  a_text_nullable TEXT,
  a_time TIME NOT NULL,
  a_time_nullable TIME,
  a_varchar VARCHAR NOT NULL,
  a_varchar_nullable VARCHAR
);

-- views
CREATE VIEW a_view_of_everything AS
  SELECT * FROM a_bit_of_everything;

CREATE VIEW a_view_of_everything_some AS
  SELECT a_bool, a_text FROM a_bit_of_everything;

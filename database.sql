DROP TABLE IF EXISTS brands;
CREATE TABLE brands(
  id   INTEGER      PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(128) NOT NULL UNIQUE
);

DROP TABLE IF EXISTS stores;
CREATE TABLE stores(
  id   INTEGER      PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(128) NOT NULL UNIQUE
);

DROP TABLE IF EXISTS products;
CREATE TABLE products(
  id    INTEGER      PRIMARY KEY AUTOINCREMENT,
  name  VARCHAR(128) NOT NULL,
  extra VARCHAR(128) NOT NULL DEFAULT "",
  unit  INTEGER      NOT NULL,

  UNIQUE(name, extra)
);

DROP TABLE IF EXISTS packages;
CREATE TABLE packages(
  id         INTEGER      PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER      NOT NULL,
  brand_id   INTEGER      NOT NULL,
  extra      VARCHAR(128) NOT NULL DEFAULT "",
  amount     REAL         NOT NULL DEFAULT 1,
  barcode    VARCHAR(32)  NULL UNIQUE,

  UNIQUE(product_id, brand_id, extra, amount),

  FOREIGN KEY(product_id) REFERENCES products(id),
  FOREIGN KEY(brand_id)   REFERENCES brands(id)
);

DROP TABLE IF EXISTS prices;
CREATE TABLE prices(
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  store_id   INTEGER NOT NULL,
  package_id INTEGER NOT NULL,
  price      INTEGER NOT NULL,
  date       DATE    NOT NULL,
  origin     INTEGER NOT NULL,

  FOREIGN KEY(store_id)   REFERENCES stores(id),
  FOREIGN KEY(package_id) REFERENCES packages(id)
);

INSERT INTO brands(id, name) VALUES(0, "");

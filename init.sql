CREATE TABLE couriers_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(16) NOT NULL,
    weight FLOAT NOT NULL
);

INSERT INTO couriers_types(name, weight) VALUES ('foot', 10);
INSERT INTO couriers_types(name, weight) VALUES ('bike', 15);
INSERT INTO couriers_types(name, weight) VALUES ('car', 50);

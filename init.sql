CREATE TABLE couriers_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(16) NOT NULL,
    weight FLOAT NOT NULL,
    price INTEGER NOT NULL
);

INSERT INTO couriers_types(name, weight, price) VALUES ('foot', 10, 2);
INSERT INTO couriers_types(name, weight, price) VALUES ('bike', 15, 5);
INSERT INTO couriers_types(name, weight, price) VALUES ('car', 50, 9);

-- Table: locations
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL
);

-- Table: clients
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: bike_types
CREATE TABLE bike_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL 
);

-- Table: discounts
CREATE TABLE discounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    percentage NUMERIC(5, 2) NOT NULL CHECK (percentage BETWEEN 0 AND 100),
    valid_from DATE,
    valid_to DATE
);

-- Table: bikes
CREATE TABLE bikes (
    id SERIAL PRIMARY KEY,
    model VARCHAR(100) NOT NULL,
    type_id INT REFERENCES bike_types(id),
    location_id INT REFERENCES locations(id),
    status VARCHAR(20) NOT NULL DEFAULT 'available', 
    daily_price NUMERIC(10, 2) NOT NULL
);

-- Table: rentals
CREATE TABLE rentals (
    id SERIAL PRIMARY KEY,
    client_id INT REFERENCES clients(id),
    bike_id INT REFERENCES bikes(id),
    rental_start TIMESTAMP NOT NULL,
    rental_end TIMESTAMP,
    total_price NUMERIC(10, 2),
    location_pickup_id INT REFERENCES locations(id),
    location_dropoff_id INT REFERENCES locations(id),
    discount_id INT REFERENCES discounts(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active' 
);

-- Table: maintenance_logs
CREATE TABLE maintenance_logs (
    id SERIAL PRIMARY KEY,
    bike_id INT REFERENCES bikes(id),
    description TEXT NOT NULL,
    maintenance_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: bike_accessories
CREATE TABLE bike_accessories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    daily_price NUMERIC(10, 2)
);

-- Table: rental_accessories 
CREATE TABLE rental_accessories (
    rental_id INT REFERENCES rentals(id),
    accessory_id INT REFERENCES bike_accessories(id),
    quantity INT DEFAULT 1,
    PRIMARY KEY (rental_id, accessory_id)
);
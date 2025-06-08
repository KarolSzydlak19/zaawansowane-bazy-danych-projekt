-- Table: locations
CREATE TABLE locations (
    id SERIAL PRIMARY KEY, -- Unique identifier for the location
    city VARCHAR(100) NOT NULL, -- Name of the city where the location is
    address TEXT NOT NULL -- Specific street address of the location
);

-- Table: clients
CREATE TABLE clients (
    id SERIAL PRIMARY KEY, -- Unique identifier for the client
    full_name VARCHAR(100) NOT NULL, -- Full name of the client
    email VARCHAR(100) UNIQUE NOT NULL, -- Email address of the client 
    phone VARCHAR(20), -- Phone number of the client
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp of when the client was registered
);

-- Table: bike_types
CREATE TABLE bike_types (
    id SERIAL PRIMARY KEY, -- Unique identifier for the bike type
    name VARCHAR(50) NOT NULL -- Name of the bike type (e.g., mountain, road, electric)
);

-- Table: discounts
CREATE TABLE discounts (
    id SERIAL PRIMARY KEY, -- Unique identifier for the discount
    name VARCHAR(100) NOT NULL, -- Name of the discount (e.g., "Summer Promo")
    description TEXT, -- Detailed description of the discount
    percentage NUMERIC(5, 2) NOT NULL CHECK (percentage BETWEEN 0 AND 100), -- Discount percentage (0–100%)
    valid_from DATE, -- Start date when the discount is valid
    valid_to DATE -- End date when the discount expires
);

-- Table: bikes
CREATE TABLE bikes (
    id SERIAL PRIMARY KEY, -- Unique identifier for the bike
    model VARCHAR(100) NOT NULL, -- Model name of the bike
    type_id INT REFERENCES bike_types(id), -- Foreign key referencing the bike type
    location_id INT REFERENCES locations(id), -- Foreign key indicating the current location of the bike
    status VARCHAR(20) NOT NULL DEFAULT 'available', -- Status of the bike (e.g., available, rented, maintenance)
    daily_price NUMERIC(10, 2) NOT NULL -- Rental price per day for the bike
);

-- Table: rentals
CREATE TABLE rentals (
    id SERIAL PRIMARY KEY, -- Unique identifier for the rental transaction
    client_id INT REFERENCES clients(id), -- Foreign key referencing the renting client
    bike_id INT REFERENCES bikes(id), -- Foreign key referencing the rented bike
    rental_start TIMESTAMP NOT NULL, -- Timestamp when the rental started
    rental_end TIMESTAMP, -- Timestamp when the rental ended (nullable for ongoing rentals)
    total_price NUMERIC(10, 2), -- Total price charged for the rental
    location_pickup_id INT REFERENCES locations(id), -- Foreign key indicating the pickup location
    location_dropoff_id INT REFERENCES locations(id), -- Foreign key indicating the drop-off location
    discount_id INT REFERENCES discounts(id), -- Foreign key referencing any applied discount
    status VARCHAR(20) NOT NULL DEFAULT 'active' -- Status of the rental (e.g., active, completed, cancelled)
);

-- Table: maintenance_logs
CREATE TABLE maintenance_logs (
    id SERIAL PRIMARY KEY, -- Unique identifier for the maintenance log entry
    bike_id INT REFERENCES bikes(id), -- Foreign key referencing the bike that was serviced
    description TEXT NOT NULL, -- Description of the maintenance work performed
    maintenance_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp when maintenance was performed
);

-- Table: bike_accessories
CREATE TABLE bike_accessories (
    id SERIAL PRIMARY KEY, -- Unique identifier for the accessory
    name VARCHAR(100) NOT NULL, -- Name of the accessory (e.g., helmet, child seat)
    daily_price NUMERIC(10, 2) -- Rental price per day for the accessory
);

-- Table: rental_accessories 
CREATE TABLE rental_accessories (
    rental_id INT REFERENCES rentals(id), -- Foreign key referencing the rental transaction
    accessory_id INT REFERENCES bike_accessories(id), -- Foreign key referencing the accessory
    quantity INT DEFAULT 1, -- Number of units of this accessory rented
    PRIMARY KEY (rental_id, accessory_id) -- Composite primary key to uniquely identify accessory rentals per rental
);

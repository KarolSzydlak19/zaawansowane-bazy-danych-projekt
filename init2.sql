-- Create the 'Movie' table to store information about movies
CREATE TABLE Movie (
    movie_id SERIAL PRIMARY KEY, -- Unique identifier for each movie
    title VARCHAR(255) NOT NULL, -- Title of the movie (cannot be null)
    duration INT NOT NULL CHECK (duration BETWEEN 30 AND 240), -- Duration of the movie (must be between 30 and 240 minutes)
    director VARCHAR(255), -- Director of the movie (optional)
    year_of_making INT CHECK (year_of_making >= 1888), -- Year the movie was made (must be 1888 or later)
    age_limit INT CHECK (age_limit IN (7, 10, 13, 18)) -- Age limit for the movie (can only be one of the predefined values)
);

-- Create the 'Theaters' table to store information about theaters
CREATE TABLE Theaters (
    theater_id SERIAL PRIMARY KEY, -- Unique identifier for each theater, it is a name of a place not a person 
    name VARCHAR(100) UNIQUE NOT NULL, -- Name of the theater (must be unique and not null)
    capacity INT NOT NULL CHECK (capacity > 0) -- Theater capacity (must be a positive number)
);

-- Create the 'Seats' table to store information about seats in each theater
CREATE TABLE Seats (
    seat_id SERIAL PRIMARY KEY, -- Unique identifier for each seat
    theater_id INT NOT NULL REFERENCES Theaters(theater_id) ON DELETE CASCADE, -- Foreign key to Theaters table (if the theater is deleted, its seats will be deleted too)
    row_number INT NOT NULL, -- Row number for the seat
    seat_number INT NOT NULL, -- Seat number within the row, an INTEGER
    is_handicap BOOLEAN DEFAULT FALSE, -- Whether the seat is a handicap-accessible seat (default is FALSE)
    UNIQUE (theater_id, row_number, seat_number) -- Ensure that each seat in a specific row and theater is unique
);

-- Create the 'Schedule' table to store the movie showtimes in theaters
CREATE TABLE Schedule (
    schedule_id SERIAL PRIMARY KEY, -- Unique identifier for each schedule entry
    theater_id INT NOT NULL REFERENCES Theaters(theater_id), -- Foreign key to Theaters table
    movie_id INT NOT NULL REFERENCES Movie(movie_id), -- Foreign key to Movie table
    show_date DATE NOT NULL, -- Date of the movie showing
    show_time TIME NOT NULL -- Time of the movie showing
);

-- Create the 'Tickets' table to store ticket information for scheduled shows
CREATE TABLE Tickets (
    ticket_id SERIAL PRIMARY KEY, -- Unique identifier for each ticket
    schedule_id INT NOT NULL REFERENCES Schedule(schedule_id) ON DELETE CASCADE, -- Foreign key to Schedule table (if a schedule is deleted, its tickets will be deleted too)
    seat_id INT NOT NULL REFERENCES Seats(seat_id), -- Foreign key to Seats table
    price NUMERIC(6, 2) NOT NULL CHECK (price > 0), -- Price of the ticket (must be greater than 0)
    UNIQUE (schedule_id, seat_id) -- Ensure that each ticket is unique for a specific schedule and seat
);

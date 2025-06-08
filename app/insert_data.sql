INSERT INTO locations (city, address) VALUES ('Jas³o', 'ulica Górna 68');
INSERT INTO clients (full_name, email, phone, created_at) VALUES ('Adrianna Dryga³a', 'agnieszka97@example.org', '602 402 147', '1995-09-28 14:49:40');
INSERT INTO bike_types (name) VALUES ('Tobiasz');
INSERT INTO discounts (name, description, percentage, valid_from, valid_to) VALUES ('Limited Discount', 'Zabawa czy ciê¿ar a wspania³y. Obwód ziarno nadmierny wstyd zbo¿e my. Dzieliæ jadalny ludowy przestêpstwo.', '27.696029287622', '1976-07-28', '2018-09-10');
INSERT INTO bikes (model, type_id, location_id, status, daily_price) VALUES ('model_variant', (SELECT id FROM bike_types ORDER BY RANDOM() LIMIT 1), (SELECT id FROM locations ORDER BY RANDOM() LIMIT 1), ' refurbished', '6842678.202');
INSERT INTO rentals (client_id, bike_id, rental_start, rental_end, total_price, location_pickup_id, location_dropoff_id, discount_id, status) VALUES ((SELECT id FROM clients ORDER BY RANDOM() LIMIT 1), (SELECT id FROM bikes ORDER BY RANDOM() LIMIT 1), '1994-02-14 20:37:17', '1998-07-10 18:15:30', '2894401.1443', (SELECT id FROM locations ORDER BY RANDOM() LIMIT 1), (SELECT id FROM locations ORDER BY RANDOM() LIMIT 1), (SELECT id FROM discounts ORDER BY RANDOM() LIMIT 1), 'refunded');
INSERT INTO maintenance_logs (bike_id, description, maintenance_date) VALUES ((SELECT id FROM bikes ORDER BY RANDOM() LIMIT 1), 'Installation', '2011-03-26 02:32:16');
INSERT INTO bike_accessories (name, daily_price) VALUES ('Filip', '1802268.2');
INSERT INTO rental_accessories (rental_id, accessory_id, quantity) VALUES ((SELECT id FROM rentals ORDER BY RANDOM() LIMIT 1), (SELECT id FROM bike_accessories ORDER BY RANDOM() LIMIT 1), '6784');

CREATE TABLE `users` (
  `id` integer PRIMARY KEY,
  `first_name` varchar(255),
  `last_name` varchar(255),
  `email` varchar(255),
  `password` varchar[255],
  `role` varchar(255),
  `created_at` timestamp
);

CREATE TABLE `account` (
  `id` integer PRIMARY KEY,
  `id_of_user` integer UNIQUE,
  `balance` integer,
  `category` varchar(255),
  `history_of_transaction` varchar(255)
);

CREATE TABLE `admin` (
  `id` integer PRIMARY KEY,
  `password` varchar(255)
);

CREATE TABLE `transaction` (
  `id` integer PRIMARY KEY,
  `amount_of_transaction` varchar(255),
  `type_of_transacton` varchar(255),
  `description` varchar(255),
  `date` date
);

ALTER TABLE `account` ADD FOREIGN KEY (`id_of_user`) REFERENCES `users` (`id`);

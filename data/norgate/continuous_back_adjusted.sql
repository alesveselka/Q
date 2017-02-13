DROP TABLE IF EXISTS `continuous_back_adjusted`;

CREATE TABLE `continuous_back_adjusted`(
  `id` int NOT NULL AUTO_INCREMENT,
  `market_id` int NOT NULL,
  `roll_strategy` varchar(255) NULL,
  `price_date` date NOT NULL,
  `open_price` decimal(19,4) NULL,
  `high_price` decimal(19,4) NULL,
  `low_price` decimal(19,4) NULL,
  `last_price` decimal(19,4) NULL,
  `settle_price` decimal(19,4) NULL,
  `volume` bigint NULL,
  `open_interest` bigint NULL,
  `created_date` datetime NOT NULL,
  `last_updated_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY `market_id_fk` (`market_id`) REFERENCES `market`(`id`) ON DELETE RESTRICT,
  KEY `index_market_id` (`market_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
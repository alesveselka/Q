DROP TABLE IF EXISTS `continuous_adjusted`;

CREATE TABLE `continuous_adjusted`(
  `id` int NOT NULL AUTO_INCREMENT,
  `market_id` int NOT NULL,
  `roll_strategy_id` int NOT NULL,
  `code` varchar(8) NOT NULL,
  `price_date` date NOT NULL,
  `open_price` double NULL,
  `high_price` double NULL,
  `low_price` double NULL,
  `last_price` double NULL,
  `settle_price` double NULL,
  `volume` bigint NULL,
  `open_interest` bigint NULL,
  `created_date` datetime NOT NULL,
  `last_updated_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY `market_id_fk` (`market_id`) REFERENCES `market`(`id`) ON DELETE CASCADE,
  KEY `index_market_id` (`market_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

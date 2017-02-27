DROP TABLE IF EXISTS `currency`;

CREATE TABLE `currency`(
  `id` int NOT NULL AUTO_INCREMENT,
  `currency_pair_id` int NOT NULL,
  `price_date` date NOT NULL,
  `open_price` decimal(24,16) NULL,
  `high_price` decimal(24,16) NULL,
  `low_price` decimal(24,16) NULL,
  `last_price` decimal(24,16) NULL,
  `created_date` datetime NOT NULL,
  `last_updated_date` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

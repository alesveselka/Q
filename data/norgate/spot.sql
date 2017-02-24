DROP TABLE IF EXISTS `spot`;

CREATE TABLE `spot`(
  `id` int NOT NULL AUTO_INCREMENT,
  `spot_market_id` int NOT NULL,
  `price_date` date NOT NULL,
  `open_price` decimal(20,10) NULL,
  `high_price` decimal(20,10) NULL,
  `low_price` decimal(20,10) NULL,
  `last_price` decimal(20,10) NULL,
  `settle_price` decimal(20,10) NULL,
  `created_date` datetime NOT NULL,
  `last_updated_date` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

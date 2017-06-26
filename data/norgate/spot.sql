DROP TABLE IF EXISTS `spot`;

CREATE TABLE `spot`(
  `id` int NOT NULL AUTO_INCREMENT,
  `spot_market_id` int NOT NULL,
  `price_date` date NOT NULL,
  `open_price` double NULL,
  `high_price` double NULL,
  `low_price` double NULL,
  `last_price` double NULL,
  `settle_price` double NULL,
  `created_date` datetime NOT NULL,
  `last_updated_date` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

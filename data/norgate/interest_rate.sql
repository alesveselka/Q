DROP TABLE IF EXISTS `interest_rate`;

CREATE TABLE `interest_rate`(
  `id` int NOT NULL AUTO_INCREMENT,
  `currency_id` int NOT NULL,
  `price_date` date NOT NULL,
  `immediate_rate` decimal(6,4) NULL,
  `three_months_rate` decimal(6,4) NULL,
  `created_date` datetime NOT NULL,
  `last_updated_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `index_currency_id` (`currency_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

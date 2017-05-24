DROP TABLE IF EXISTS `investment_universe`;

CREATE TABLE `investment_universe`(
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `contract_start_date` date NOT NULL,
  `data_start_date` date NOT NULL,
  `market_ids` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

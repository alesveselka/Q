DROP TABLE IF EXISTS `market_equity`;

CREATE TABLE `market_equity`(
  `id` int NOT NULL AUTO_INCREMENT,
  `simulation_id` int NOT NULL,
  `market_id` int NOT NULL,
  `contract` varchar(16) NULL,
  `date` date NOT NULL,
  `equity` decimal(40,30) NOT NULL,
  `marked_to_market` decimal(40,30) NULL,
  `commissions` decimal(40,30) NULL,
  `positions` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `index_market` (`market_id`, `date`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

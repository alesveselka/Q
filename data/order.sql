DROP TABLE IF EXISTS `order`;

CREATE TABLE `order`(
  `id` int NOT NULL AUTO_INCREMENT,
  `simulation_id` int NOT NULL,
  `market_id` int NOT NULL,
  `contract` varchar(32) NULL,
  `type` varchar(8) NOT NULL,
  `signal_type` varchar(16) NOT NULL,
  `date` date NOT NULL,
  `price` decimal(20,10) NOT NULL,
  `quantity` int NOT NULL,
  `result_type` varchar(16) NOT NULL,
  `result_price` decimal(20,10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

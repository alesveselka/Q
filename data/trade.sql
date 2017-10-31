DROP TABLE IF EXISTS `trade`;

CREATE TABLE `trade`(
  `id` int NOT NULL AUTO_INCREMENT,
  `simulation_id` int NOT NULL,
  `market_id` int NOT NULL,
  `contract` varchar(32) NULL,
  `date` date NOT NULL,
  `order_price` double NOT NULL,
  `order_quantity` int NOT NULL,
  `result_type` varchar(16) NOT NULL,
  `result_price` decimal(20,10) NOT NULL,
  `result_quantity` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

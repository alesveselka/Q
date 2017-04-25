DROP TABLE IF EXISTS `trade`;

CREATE TABLE `trade`(
  `id` int NOT NULL AUTO_INCREMENT,
  `market_id` int NOT NULL,
  `direction` varchar(8) NOT NULL,
  `quantity` int NOT NULL,
  `enter_date` date NOT NULL,
  `enter_price` decimal(40,30) NOT NULL,
  `enter_slip` decimal(40,30) NOT NULL,
  `exit_date` date NOT NULL,
  `exit_price` decimal(40,30) NOT NULL,
  `exit_slip` decimal(40,30) NOT NULL,
  `commissions` decimal(40,30) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `position`;

CREATE TABLE `position`(
  `id` int NOT NULL AUTO_INCREMENT,
  `market_id` int NOT NULL,
  `direction` varchar(8) NOT NULL,
  `enter_date` date NOT NULL,
  `enter_price` decimal(20,10) NOT NULL,
  `exit_date` date NULL,
  `exit_price` decimal(20,10) NULL,
  `quantity` int NOT NULL,
  `pnl` decimal(20,10) NOT NULL,
  `commissions` decimal(20,10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

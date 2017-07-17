DROP TABLE IF EXISTS `equity`;

CREATE TABLE `equity`(
  `id` int NOT NULL AUTO_INCREMENT,
  `simulation_id` int NOT NULL,
  `date` date NOT NULL,
  `equity` decimal(40,30) NOT NULL,
  `available_funds` decimal(40,30) NOT NULL,
  `balances` varchar(600) NOT NULL,
  `margins` varchar(600) NULL,
  `marked_to_market` varchar(600) NULL,
  `commissions` varchar(255) NULL,
  `fx_translations` varchar(255) NULL,
  `margin_interest` varchar(600) NULL,
  `balance_interest` varchar(600) NULL,
  `rates` varchar(255) NULL,
  `margin_ratio` decimal(20,10) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

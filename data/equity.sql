DROP TABLE IF EXISTS `equity`;

CREATE TABLE `equity`(
  `id` int NOT NULL AUTO_INCREMENT,
  `simulation_id` int NOT NULL,
  `date` date NOT NULL,
  `equity` decimal(40,30) NOT NULL,
  `available_funds` decimal(40,30) NOT NULL,
  `balances` TEXT CHARACTER SET utf8 NOT NULL,
  `margins` TEXT CHARACTER SET utf8 NULL,
  `marked_to_market` TEXT CHARACTER SET utf8 NULL,
  `commissions` TEXT CHARACTER SET utf8 NULL,
  `fx_translations` TEXT CHARACTER SET utf8 NULL,
  `margin_interest` TEXT CHARACTER SET utf8 NULL,
  `balance_interest` TEXT CHARACTER SET utf8 NULL,
  `rates` TEXT CHARACTER SET utf8 NULL,
  `margin_ratio` decimal(20,10) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

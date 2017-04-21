DROP TABLE IF EXISTS `equity`;

CREATE TABLE `equity`(
  `id` int NOT NULL AUTO_INCREMENT,
  `base_currency` varchar(32) NOT NULL,
  `date` date NOT NULL,
  `equity` decimal(40,30) NOT NULL,
  `balances` TEXT CHARACTER SET utf8 NOT NULL,
  `margins` TEXT CHARACTER SET utf8 NULL,
  `margin_ratio` decimal(20,10) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

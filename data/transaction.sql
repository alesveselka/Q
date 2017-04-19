DROP TABLE IF EXISTS `transaction`;

CREATE TABLE `transaction`(
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(32) NOT NULL,
  `account_action` varchar(16) NOT NULL,
  `date` date NOT NULL,
  `amount` decimal(40,30) NOT NULL,
  `currency` varchar(8) NOT NULL,
  `context` TEXT CHARACTER SET utf8,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

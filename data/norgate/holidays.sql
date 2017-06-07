DROP TABLE IF EXISTS `holidays`;

CREATE TABLE `holidays`(
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `description` varchar(255) NOT NULL,
  `exchanges` varchar(255) NULL,
  `country` varchar(32) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

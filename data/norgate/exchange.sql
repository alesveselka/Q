DROP TABLE IF EXISTS `exchange`;

CREATE TABLE `exchange`(
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(32) NOT NULL,
  `ex_code` varchar(32) NULL,
  `name` varchar(255) NOT NULL,
  `city` varchar(255) NULL,
  `country` varchar(255) NULL,
  `timezone` varchar(32) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

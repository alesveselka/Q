DROP TABLE IF EXISTS `study`;

CREATE TABLE `study`(
  `id` int NOT NULL AUTO_INCREMENT,
  `market_id` int NOT NULL,
  `market_code` varchar(8) NOT NULL,
  `date` date NOT NULL,
  `value` decimal(20,10) NOT NULL,
  `value_2` decimal(20,10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

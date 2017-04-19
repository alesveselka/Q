DROP TABLE IF EXISTS `order`;

CREATE TABLE `order`(
  `id` int NOT NULL AUTO_INCREMENT,
  `market_id` int NOT NULL,
  `type` varchar(8) NOT NULL,
  `date` date NOT NULL,
  `price` decimal(40,30) NOT NULL,
  `quantity` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `standard_roll_schedule`;

CREATE TABLE `standard_roll_schedule`(
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `market_id` int NOT NULL,
  `roll_out_month` varchar(8) NOT NULL,
  `roll_in_month` varchar(8) NOT NULL,
  `month` varchar(8) NOT NULL,
  `day` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `index_market_id` (`market_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

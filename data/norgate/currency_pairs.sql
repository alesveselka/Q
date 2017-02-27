DROP TABLE IF EXISTS `currency_pairs`;

CREATE TABLE `currency_pairs`(
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(8) NOT NULL,
  `name` varchar(255) NOT NULL,
  `group_id` int NOT NULL,
  `first_data_date` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `index_group_id` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `spot_market`;

CREATE TABLE `spot_market`(
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `code` varchar(32) NOT NULL,
  `group_id` int NOT NULL,
  `first_data_date` date NOT NULL,
  `notes` varchar(255) NULL,
  PRIMARY KEY (`id`),
  KEY `index_group_id` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

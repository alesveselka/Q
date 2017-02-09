DROP TABLE IF EXISTS `holidays`;

CREATE TABLE `holidays`(
  `id` int NOT NULL AUTO_INCREMENT,
  `exchange_id` int NOT NULL,
  `holiday` date NOT NULL,
  `name` varchar(255) NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY `exchange_id_fk` (`exchange_id`) REFERENCES `exchange`(`id`) ON DELETE RESTRICT,
  KEY `index_exchange_id` (`exchange_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

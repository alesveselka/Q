DROP TABLE IF EXISTS `spot`;

CREATE TABLE `spot`(
  `id` int NOT NULL AUTO_INCREMENT,
  `market_id` int NOT NULL,
  `code` varchar(32) NOT NULL,
  `note` varchar(255) NULL,
  `created_date` datetime NOT NULL,
  `last_updated_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY `market_id_fk` (`market_id`) REFERENCES `market`(`id`) ON DELETE RESTRICT,
  KEY `index_market_id` (`market_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `market`;

CREATE TABLE `market`(
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `code` varchar(32) NOT NULL,
  `instrument` varchar(255) NOT NULL,
  `data_vendor` varchar(255) NULL,
  `exchange_id` int NOT NULL,
  `group_id` int NOT NULL,
  `contract_size` varchar(255) NULL,
  `quotation` varchar(255) NULL,
  `tick_size` varchar(255) NOT NULL,
  `tick_value` decimal(19,4) NOT NULL,
  `point_value` decimal(19,4) NOT NULL,
  `currency` varchar(32) NOT NULL,
  `last_trading_day` varchar(255) NULL,
  `first_notice_day` varchar(255) NULL,
  `trading_hours` varchar(255) NULL,
  `session` varchar(255) NULL,
  `volume_offset` tinyint NOT NULL DEFAULT 0,
  `oi_offset` tinyint NOT NULL DEFAULT 0,
  `delivery_months` varchar(24) NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY `exchange_id_fk` (`exchange_id`) REFERENCES `exchange`(`id`) ON DELETE RESTRICT,
  FOREIGN KEY `group_id_fk` (`group_id`) REFERENCES `group`(`id`) ON DELETE RESTRICT,
  KEY `index_exchange_id` (`exchange_id`),
  KEY `index_group_id` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
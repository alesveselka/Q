CREATE TABLE `daily_price` (
`id` int NOT NULL AUTO_INCREMENT,
`data_vendor_id` int NOT NULL,
`symbol_id` int NOT NULL,
`price_date` datetime NOT NULL,
`created_date` datetime NOT NULL,
`last_updated_date` datetime NOT NULL,
`open_price` decimal(19,4) NULL,
`high_price` decimal(19,4) NULL,
`low_price` decimal(19,4) NULL,
`close_price` decimal(19,4) NULL,
`adj_close_price` decimal(19,4) NULL,
`volume` bigint NULL,
PRIMARY KEY (`id`),
KEY `index_data_vendor_id` (`data_vendor_id`),
KEY `index_symbol_id` (`symbol_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

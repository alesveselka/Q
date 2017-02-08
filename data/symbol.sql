DROP TABLE IF EXISTS symbol;

CREATE TABLE `symbol` (
`id` int NOT NULL AUTO_INCREMENT,
`exchange_id` int NULL,
`ticker` varchar(32) NOT NULL,
`instrument` varchar(64) NOT NULL,
`name` varchar(255) NULL,
`sector` varchar(255) NULL,
`currency` varchar(32) NULL,
`timezone_offset` time NULL,
`created_date` datetime NOT NULL,
`last_updated_date` datetime NOT NULL,
PRIMARY KEY (`id`),
KEY `index_exchange_id` (`exchange_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

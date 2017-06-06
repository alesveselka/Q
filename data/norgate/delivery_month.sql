DROP TABLE IF EXISTS `delivery_month`;

CREATE TABLE `delivery_month`(
  `code` varchar(4) NOT NULL,
  `name` varchar(32) NULL,
  `short_name` varchar(8) NULL,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `data_codes`;

CREATE TABLE `data_codes`(
  `code` varchar(4) NOT NULL,
  `appendix` varchar(4) NOT NULL,
  `name` varchar(32) NULL,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

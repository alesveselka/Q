DROP TABLE IF EXISTS `correlation_matrix`;

CREATE TABLE `correlation_matrix`(
  `id` int NOT NULL AUTO_INCREMENT,
  `investment_universe_name` varchar(16) NOT NULL,
  `date` date NOT NULL,
  `lookback` int NOT NULL,
  `categories` varchar(512) NOT NULL,
  `movement_market_correlations` TEXT CHARACTER SET utf8 NULL,
  `movement_market_correlations_ew` TEXT CHARACTER SET utf8 NULL,
  `movement_group_correlations` TEXT CHARACTER SET utf8 NULL,
  `movement_group_correlations_ew` TEXT CHARACTER SET utf8 NULL,
  `dev_market_correlations` TEXT CHARACTER SET utf8 NULL,
  `dev_market_correlations_ew` TEXT CHARACTER SET utf8 NULL,
  `dev_group_correlations` TEXT CHARACTER SET utf8 NULL,
  `dev_group_correlations_ew` TEXT CHARACTER SET utf8 NULL,
  PRIMARY KEY (`id`),
  KEY `index_lookback_universe` (`investment_universe_name`, `lookback`, `date`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

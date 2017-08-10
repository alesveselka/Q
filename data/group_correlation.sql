DROP TABLE IF EXISTS `group_correlation`;

CREATE TABLE `group_correlation`(
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `lookback` int NOT NULL,
  `investment_universe_name` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `returns` double NULL,
  `movement_volatility` double NULL,
  `dev_volatility` double NULL,
  `movement_correlations` TEXT CHARACTER SET utf8 NULL,
  `movement_correlations_ew` TEXT CHARACTER SET utf8 NULL,
  `dev_correlations` TEXT CHARACTER SET utf8 NULL,
  `dev_correlations_ew` TEXT CHARACTER SET utf8 NULL,
  PRIMARY KEY (`id`),
  KEY `index_lookback` (`lookback`),
  KEY `index_lookback_universe` (`lookback`, `investment_universe_name`),
  KEY `index_group_id` (`group_id`, `lookback`, `investment_universe_name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

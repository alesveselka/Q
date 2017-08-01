DROP TABLE IF EXISTS `group_correlation`;

CREATE TABLE `group_correlation`(
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `lookback` int NOT NULL,
  `date` date NOT NULL,
  `movement_volatility` double NULL,
  `dev_volatility` double NULL,
  `movement_correlations` TEXT CHARACTER SET utf8 NULL,
  `dev_correlations` TEXT CHARACTER SET utf8 NULL,
  PRIMARY KEY (`id`),
  KEY `index_lookback` (`lookback`),
  KEY `index_group_id` (`group_id`, `lookback`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

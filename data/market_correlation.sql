DROP TABLE IF EXISTS `market_correlation`;

CREATE TABLE `market_correlation`(
  `market_id` int NOT NULL,
  `market_code` varchar(8) NOT NULL,
  `lookback` int NOT NULL,
  `date` date NOT NULL,
  `movement_volatility` double NULL,
  `dev_volatility` double NULL,
  `movement_correlations` TEXT CHARACTER SET utf8 NULL,
  `dev_correlations` TEXT CHARACTER SET utf8 NULL,
  PRIMARY KEY (market_id, market_code, lookback, date)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

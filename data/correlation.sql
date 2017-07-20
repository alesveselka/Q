DROP TABLE IF EXISTS `correlation`;

CREATE TABLE `correlation`(
  `market_id` int NOT NULL,
  `market_code` varchar(8) NOT NULL,
  `roll_strategy_id` int NOT NULL,
  `date` date NOT NULL,
  `volatility` double NULL,
  `correlations` TEXT CHARACTER SET utf8 NULL,
  PRIMARY KEY (market_id, market_code, roll_strategy_id, date)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

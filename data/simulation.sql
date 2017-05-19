DROP TABLE IF EXISTS `simulation`;

CREATE TABLE `simulation`(
  `trading_strategy_id` int NOT NULL,
  `investment_universe_id` int NOT NULL,
  PRIMARY KEY (`trading_strategy_id`, `investment_universe_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

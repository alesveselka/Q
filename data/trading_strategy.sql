DROP TABLE IF EXISTS `trading_strategy`;

CREATE TABLE `trading_strategy`(
  `id` int NOT NULL AUTO_INCREMENT,
  `trading_model_id` int NOT NULL,
  `params` TEXT CHARACTER SET utf8,
  `studies` TEXT CHARACTER SET utf8,
  `roll_strategy_id` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

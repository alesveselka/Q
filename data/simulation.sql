DROP TABLE IF EXISTS `simulation`;

CREATE TABLE `simulation`(
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `params` TEXT CHARACTER SET utf8,
  `trading_model` VARCHAR(255) NOT NULL,
  `trading_params` TEXT CHARACTER SET utf8,
  `studies` TEXT CHARACTER SET utf8,
  `roll_strategy_id` int NOT NULL,
  `investment_universe` VARCHAR(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

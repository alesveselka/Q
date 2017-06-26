DROP TABLE IF EXISTS `contract_roll`;

CREATE TABLE `contract_roll`(
  `id` int NOT NULL AUTO_INCREMENT,
  `market_id` int NOT NULL,
  `roll_strategy_id` int NOT NULL,
  `date` date NOT NULL,
  `gap` double NULL,
  `roll_out_contract` VARCHAR(32) NULL,
  `roll_in_contract` VARCHAR(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

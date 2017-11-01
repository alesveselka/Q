DROP TABLE IF EXISTS `positions`;

CREATE TABLE `positions`(
  `id` int NOT NULL AUTO_INCREMENT,
  `simulation_id` int NOT NULL,
  `date` date NOT NULL,
  `positions` varchar(2400) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

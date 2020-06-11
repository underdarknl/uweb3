CREATE TABLE `test` (
  `name` varchar(50) NOT NULL,
  `modulename` varchar(50) NOT NULL,
  `args` varchar(255) DEFAULT NULL,
  `kwargs` varchar(255) DEFAULT NULL,
  `created` timestamp NULL DEFAULT NULL,
  `creating` timestamp NULL DEFAULT NULL,
  `data` text,
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`ID`)
 ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

CREATE TABLE `users` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `author` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(45) NOT NULL,
  `admin` enum('true','false') CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `password` varchar(255) DEFAULT NULL,
  `salt` varchar(45) DEFAULT NULL,
  `active` enum('true','false') CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
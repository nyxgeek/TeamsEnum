-- MySQL dump 10.13  Distrib 8.0.41, for Linux (x86_64)
--
-- Host: localhost    Database: teamsdb
-- ------------------------------------------------------
-- Server version       8.0.41-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `user_presence`
--

DROP TABLE IF EXISTS `user_presence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_presence` (
  `id` int NOT NULL AUTO_INCREMENT,
  `teams_guid` varchar(36) NOT NULL,
  `availability` varchar(16) NOT NULL,
  `ooo_enabled` tinyint(1) NOT NULL,
  `device` varchar(10) NOT NULL,
  `scrape_date_unix` bigint NOT NULL,
  `scrape_date` date NOT NULL,
  `hh_period` tinyint unsigned NOT NULL,
  `qh_period` tinyint unsigned NOT NULL,
  `session` varchar(8) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_scrape_date` (`scrape_date`),
  KEY `idx_availability` (`availability`),
  KEY `idx_hh_period` (`hh_period`)
) ENGINE=InnoDB AUTO_INCREMENT=2491670 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_info_all`
--

DROP TABLE IF EXISTS `user_info_all`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_info_all` (
  `object_id` varchar(255) NOT NULL,
  `user_principal_name` varchar(255) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `display_name` varchar(255) DEFAULT NULL,
  `tenant_id` varchar(255) DEFAULT NULL,
  `co_existence_mode` varchar(50) DEFAULT NULL,
  `given_name` varchar(255) DEFAULT NULL,
  `surname` varchar(255) DEFAULT NULL,
  `account_enabled` tinyint(1) DEFAULT NULL,
  `tenant_name` varchar(255) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `scrape_date` date DEFAULT NULL,
  `scrape_time` time DEFAULT NULL,
  `scrape_date_unix` bigint DEFAULT NULL,
  `isOOO` tinyint(1) DEFAULT '0',
  `session` varchar(8) DEFAULT NULL,
  PRIMARY KEY (`object_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_ooo`
--

DROP TABLE IF EXISTS `user_ooo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_ooo` (
  `md5sum` char(32) NOT NULL,
  `teams_guid` char(36) NOT NULL,
  `scrape_date` date NOT NULL,
  `scrape_time` time NOT NULL,
  `scrape_date_unix` bigint NOT NULL,
  `length` int NOT NULL,
  `truncated` tinyint(1) NOT NULL,
  `text` varchar(1000) NOT NULL,
  PRIMARY KEY (`md5sum`),
  KEY `idx_user_date` (`teams_guid`,`scrape_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daily_stats_detailed`
--

DROP TABLE IF EXISTS `daily_stats_detailed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_stats_detailed` (
  `date` date NOT NULL,
  `hh_period` int NOT NULL,
  `qh_period` int NOT NULL,
  `r_available` int DEFAULT NULL,
  `r_busy` int DEFAULT NULL,
  `r_donotdisturb` int DEFAULT NULL,
  `r_away` int DEFAULT NULL,
  `r_offline` int DEFAULT NULL,
  `r_ooocount` int DEFAULT NULL,
  `total_users` int DEFAULT NULL,
  `r_online` int DEFAULT NULL,
  `p_available` float DEFAULT NULL,
  `p_busy` float DEFAULT NULL,
  `p_donotdisturb` float DEFAULT NULL,
  `p_away` float DEFAULT NULL,
  `p_offline` float DEFAULT NULL,
  `p_ooocount` float DEFAULT NULL,
  `p_online` float DEFAULT NULL,
  PRIMARY KEY (`date`,`hh_period`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daily_stats_summary`
--

DROP TABLE IF EXISTS `daily_stats_summary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_stats_summary` (
  `date` date NOT NULL,
  `total_users` int DEFAULT NULL,
  `total_online` int DEFAULT NULL,
  `r_available` int DEFAULT NULL,
  `r_available2hr` int DEFAULT NULL,
  `r_available4hr` int DEFAULT NULL,
  `r_alwaysavailable` int DEFAULT NULL,
  `r_alwaysoffline` int DEFAULT NULL,
  `r_ooocount` int DEFAULT NULL,
  `p_total_online` float DEFAULT NULL,
  `p_available` float DEFAULT NULL,
  `p_available2hr` float DEFAULT NULL,
  `p_available4hr` float DEFAULT NULL,
  `p_alwaysavailable` float DEFAULT NULL,
  `p_alwaysoffline` float DEFAULT NULL,
  `p_ooocount` float DEFAULT NULL,
  PRIMARY KEY (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-02-22 12:43:08

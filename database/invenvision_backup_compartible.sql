-- =====================================================================
-- InvenVision - respaldo COMPARTIBLE (datos de prueba, sin datos personales)
--
-- * Usuario de demostracion: admin@invenvision.demo (la contrasena NO esta
--   en este archivo; se entrega por separado o se cambia con
--   `python -m scripts.restablecer_password`).
-- * ATENCION: este script hace DROP TABLE IF EXISTS sobre las tablas de la
--   base `invenvision` y las vuelve a crear. Importelo solo en una base
--   nueva o cuyos datos pueda perder. Pasos: docs/restaurar-base-de-datos.md
-- * Las rutas de imagen (productos/1.png, scans/...) apuntan a archivos que
--   no se versionan; la aplicacion lo tolera ("Imagen no disponible").
-- =====================================================================
CREATE DATABASE  IF NOT EXISTS `invenvision` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `invenvision`;
-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: invenvision
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `categorias`
--

DROP TABLE IF EXISTS `categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categorias` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categorias`
--

LOCK TABLES `categorias` WRITE;
/*!40000 ALTER TABLE `categorias` DISABLE KEYS */;
INSERT INTO `categorias` VALUES (9,'azucares'),(2,'Bebidas'),(5,'Conservas'),(6,'Higiene'),(1,'Lácteos'),(4,'Limpieza'),(8,'Otros'),(7,'Panadería'),(3,'Snacks');
/*!40000 ALTER TABLE `categorias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `configuracion_alertas`
--

DROP TABLE IF EXISTS `configuracion_alertas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuracion_alertas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `dias_alerta` int NOT NULL DEFAULT '30',
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `fk_config_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `configuracion_alertas`
--

LOCK TABLES `configuracion_alertas` WRITE;
/*!40000 ALTER TABLE `configuracion_alertas` DISABLE KEYS */;
INSERT INTO `configuracion_alertas` VALUES (1,1,30);
/*!40000 ALTER TABLE `configuracion_alertas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historial_deteccion`
--

DROP TABLE IF EXISTS `historial_deteccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historial_deteccion` (
  `id` int NOT NULL AUTO_INCREMENT,
  `producto_id` int DEFAULT NULL,
  `imagen_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `texto_detectado_ocr` text COLLATE utf8mb4_unicode_ci,
  `fecha_detectada` date DEFAULT NULL,
  `confianza_ocr` decimal(5,2) DEFAULT NULL,
  `fue_corregido_manual` tinyint(1) NOT NULL DEFAULT '0',
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_historial_producto` (`producto_id`),
  CONSTRAINT `fk_historial_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historial_deteccion`
--

LOCK TABLES `historial_deteccion` WRITE;
/*!40000 ALTER TABLE `historial_deteccion` DISABLE KEYS */;
INSERT INTO `historial_deteccion` VALUES (1,1,'scans/1_17899479ebaf44438a283632516bd1a8.jpg','_—\ne SES, ]\n,\n! 3\nj i\nd','2026-10-24',50.30,1,'2026-10-25 17:17:14');
/*!40000 ALTER TABLE `historial_deteccion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos`
--

DROP TABLE IF EXISTS `productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `categoria_id` int NOT NULL,
  `codigo_barras` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `lote` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fecha_vencimiento` date NOT NULL,
  `stock` int NOT NULL DEFAULT '0',
  `imagen_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `usuario_id` int NOT NULL,
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_producto_usuario` (`usuario_id`),
  KEY `idx_productos_vencimiento` (`fecha_vencimiento`),
  KEY `idx_productos_categoria` (`categoria_id`),
  CONSTRAINT `fk_producto_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`),
  CONSTRAINT `fk_producto_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos`
--

LOCK TABLES `productos` WRITE;
/*!40000 ALTER TABLE `productos` DISABLE KEYS */;
INSERT INTO `productos` VALUES (1,'Azúcar blanca',9,'azucares','AZU-001','2026-10-24',20,'productos/1.png',1,'2026-10-25 17:00:24','2026-10-25 17:17:14');
/*!40000 ALTER TABLE `productos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `correo` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rol` enum('administrador','operador') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'operador',
  `negocio` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Administrador Demo','admin@invenvision.demo','$2b$12$zmvp7Kp57TUs2vZmEdSZBegWQD7PJwbMhZ6U5Kjqhnef9IiC3Uucm','administrador','Bodega InvenVision',1,'2026-09-14 21:39:59');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `vista_productos_estado`
--

DROP TABLE IF EXISTS `vista_productos_estado`;
/*!50001 DROP VIEW IF EXISTS `vista_productos_estado`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vista_productos_estado` AS SELECT 
 1 AS `id`,
 1 AS `nombre`,
 1 AS `categoria_id`,
 1 AS `codigo_barras`,
 1 AS `lote`,
 1 AS `fecha_vencimiento`,
 1 AS `stock`,
 1 AS `imagen_path`,
 1 AS `usuario_id`,
 1 AS `creado_en`,
 1 AS `actualizado_en`,
 1 AS `categoria_nombre`,
 1 AS `dias_restantes`,
 1 AS `estado`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `vista_productos_estado`
--

/*!50001 DROP VIEW IF EXISTS `vista_productos_estado`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 SQL SECURITY INVOKER */
/*!50001 VIEW `vista_productos_estado` AS select `p`.`id` AS `id`,`p`.`nombre` AS `nombre`,`p`.`categoria_id` AS `categoria_id`,`p`.`codigo_barras` AS `codigo_barras`,`p`.`lote` AS `lote`,`p`.`fecha_vencimiento` AS `fecha_vencimiento`,`p`.`stock` AS `stock`,`p`.`imagen_path` AS `imagen_path`,`p`.`usuario_id` AS `usuario_id`,`p`.`creado_en` AS `creado_en`,`p`.`actualizado_en` AS `actualizado_en`,`c`.`nombre` AS `categoria_nombre`,(to_days(`p`.`fecha_vencimiento`) - to_days(curdate())) AS `dias_restantes`,(case when ((to_days(`p`.`fecha_vencimiento`) - to_days(curdate())) < 0) then 'vencido' when ((to_days(`p`.`fecha_vencimiento`) - to_days(curdate())) <= 30) then 'proximo' else 'vigente' end) AS `estado` from (`productos` `p` join `categorias` `c` on((`c`.`id` = `p`.`categoria_id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-25 17:50:50

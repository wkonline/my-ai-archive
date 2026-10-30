-- MySQL dump 10.13  Distrib 26.7.0, for macos26.6 (arm64)
--
-- Host: 192.168.1.201    Database: cono
-- ------------------------------------------------------
-- Server version	8.0.38

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
-- Table structure for table `auth_role`
--

DROP TABLE IF EXISTS `auth_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_role` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `key` varchar(32) NOT NULL,
  `name` varchar(64) NOT NULL,
  `permissions` json NOT NULL,
  `menus` json NOT NULL,
  `create_time` datetime(6) NOT NULL,
  `update_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_role`
--

LOCK TABLES `auth_role` WRITE;
/*!40000 ALTER TABLE `auth_role` DISABLE KEYS */;
INSERT INTO `auth_role` VALUES (1,'admin','管理员','[\"admin_add\", \"admin_edit\", \"admin_list\", \"admin_reset\", \"auth_role_add\", \"auth_role_delete\", \"auth_role_edit\", \"auth_role_list\", \"auth_user_permission\", \"backup_database\", \"bill_file\", \"chart_bar\", \"chart_line\", \"chart_list\", \"chart_pie\", \"collection_add\", \"collection_create\", \"collection_delete\", \"collection_download_excel\", \"collection_edit\", \"collection_list\", \"company_edit\", \"company_show\", \"contract_create\", \"contract_delete\", \"contract_download_excel\", \"contract_edit\", \"contract_file_list\", \"contract_list\", \"contract_product\", \"contract_product_download_excel\", \"contract_product_multi\", \"customer_add\", \"customer_delete\", \"customer_edit\", \"customer_list\", \"delete_contract_file\", \"delivery_add\", \"delivery_delete\", \"delivery_edit\", \"delivery_list\", \"delivery_multi\", \"department_add\", \"department_delete\", \"department_edit\", \"department_list\", \"edit_contract_file\", \"electrical_file\", \"get_category_list\", \"get_collection_contracts\", \"get_collection_customers\", \"get_contract_amount\", \"get_invoice_contracts\", \"get_log\", \"get_product_model\", \"get_productcategory_product\", \"get_return_product_model\", \"get_return_product_services\", \"get_servicedetail_services\", \"highcharts\", \"invoice_add\", \"invoice_create\", \"invoice_delete\", \"invoice_edit\", \"invoice_list\", \"invoice_multi\", \"load_products\", \"mechanical_file\", \"media\", \"plan_add\", \"plan_delete\", \"plan_download_excel\", \"plan_edit\", \"plan_list\", \"print_plan\", \"product_add\", \"product_delete\", \"product_edit\", \"product_list\", \"productcategory_add\", \"productcategory_delete\", \"productcategory_edit\", \"productcategory_list\", \"productcategory_multi\", \"productlabel_add\", \"productlabel_delete\", \"productlabel_edit\", \"productlabel_list\", \"restore_database\", \"return_product_add\", \"return_product_delete\", \"return_product_download_excel\", \"return_product_edit\", \"return_product_list\", \"search_companys\", \"search_warehouses\", \"service_add\", \"service_delete\", \"service_download_excel\", \"service_edit\", \"service_list\", \"servicedetail_add\", \"servicedetail_delete\", \"servicedetail_download_excel\", \"servicedetail_edit\", \"servicedetail_list\", \"task_add\", \"task_delete\", \"task_edit\", \"task_list\", \"upload_excel\", \"user_add\", \"user_delete\", \"user_edit\", \"user_list\", \"user_reset\", \"warehouse_add\", \"warehouse_delete\", \"warehouse_edit\", \"warehouse_list\"]','[{\"url\": \"/contract/\", \"title\": \"合同管理\"}, {\"url\": \"/collection/\", \"title\": \"回款登记\"}, {\"url\": \"/invoice/\", \"title\": \"发票登记\"}, {\"url\": \"/plan/\", \"title\": \"生产计划\"}, {\"url\": \"/contract_file/\", \"title\": \"资料上传\"}, {\"url\": \"/task/\", \"title\": \"派任务单\"}, {\"url\": \"/productlabel/\", \"title\": \"产品铭牌\"}, {\"url\": \"/delivery/\", \"title\": \"入库发货\"}, {\"url\": \"/warehouse/\", \"title\": \"仓库管理\"}, {\"url\": \"/department/\", \"title\": \"部门管理\"}, {\"url\": \"/user/\", \"title\": \"用户管理\"}, {\"url\": \"/customer/\", \"title\": \"客户管理\"}, {\"url\": \"/productcategory/\", \"title\": \"产品分类\"}, {\"url\": \"/product/\", \"title\": \"产品管理\"}, {\"url\": \"/service/\", \"title\": \"售后服务\"}, {\"url\": \"/servicedetail/\", \"title\": \"维修服务\"}, {\"url\": \"/return_product/\", \"title\": \"售后返件\"}, {\"url\": \"/chart/\", \"title\": \"数据统计\"}, {\"url\": \"/database/backup/\", \"title\": \"数据备份\"}, {\"url\": \"/log/\", \"title\": \"操作日志\"}, {\"url\": \"/company/\", \"title\": \"公司信息\"}, {\"url\": \"/auth/role/\", \"title\": \"权限管理\"}, {\"url\": \"/delivery/\", \"title\": \"发货信息\"}]','2026-09-07 03:57:21.079073','2026-09-07 06:38:04.883834'),(2,'saler','业务员','[\"collection_add\", \"collection_delete\", \"collection_edit\", \"collection_list\", \"contract_add\", \"contract_delete\", \"contract_edit\", \"contract_list\", \"customer_add\", \"customer_delete\", \"customer_edit\", \"customer_list\", \"department_add\", \"department_delete\", \"department_edit\", \"department_list\", \"get_collection_contracts\", \"get_collection_customers\", \"product_add\", \"product_delete\", \"product_edit\", \"product_list\", \"productcategory_add\", \"productcategory_delete\", \"productcategory_edit\", \"productcategory_list\", \"service_add\", \"service_delete\", \"service_edit\", \"service_list\", \"servicedetail_add\", \"servicedetail_delete\", \"servicedetail_edit\", \"servicedetail_list\", \"warehouse_add\", \"warehouse_delete\", \"warehouse_edit\", \"warehouse_list\"]','[{\"url\": \"/plan/\", \"title\": \"生产计划\"}, {\"url\": \"/contract/\", \"title\": \"合同管理\"}, {\"url\": \"/collection/\", \"title\": \"回款登记\"}, {\"url\": \"/warehouse/\", \"title\": \"仓库管理\"}, {\"url\": \"/user/\", \"title\": \"用户管理\"}, {\"url\": \"/customer/\", \"title\": \"客户管理\"}, {\"url\": \"/productcategory/\", \"title\": \"产品分类\"}, {\"url\": \"/product/\", \"title\": \"产品管理\"}, {\"url\": \"/department/\", \"title\": \"部门管理\"}, {\"url\": \"/service/\", \"title\": \"售后服务\"}, {\"url\": \"/servicedetail/\", \"title\": \"维修服务\"}, {\"url\": \"/contract_file/\", \"title\": \"资料上传\"}, {\"url\": \"/productlabel/\", \"title\": \"产品铭牌\"}, {\"url\": \"/delivery/\", \"title\": \"发货信息\"}, {\"url\": \"/invoice/\", \"title\": \"发票登记\"}]','2026-09-07 03:57:21.160130','2026-09-07 06:38:04.975170'),(3,'servicer','客户经理','[\"collection_add\", \"collection_delete\", \"collection_edit\", \"collection_list\", \"contract_add\", \"contract_delete\", \"contract_edit\", \"contract_list\", \"customer_add\", \"customer_delete\", \"customer_edit\", \"customer_list\", \"department_add\", \"department_delete\", \"department_edit\", \"department_list\", \"get_collection_contracts\", \"get_collection_customers\", \"media\", \"product_add\", \"product_delete\", \"product_edit\", \"product_list\", \"productcategory_add\", \"productcategory_delete\", \"productcategory_edit\", \"productcategory_list\", \"service_add\", \"service_delete\", \"service_edit\", \"service_list\", \"servicedetail_add\", \"servicedetail_delete\", \"servicedetail_edit\", \"servicedetail_list\", \"warehouse_add\", \"warehouse_delete\", \"warehouse_edit\", \"warehouse_list\"]','[{\"url\": \"/plan/\", \"title\": \"生产计划\"}, {\"url\": \"/contract/\", \"title\": \"合同管理\"}, {\"url\": \"/collection/\", \"title\": \"回款登记\"}, {\"url\": \"/warehouse/\", \"title\": \"仓库管理\"}, {\"url\": \"/user/\", \"title\": \"用户管理\"}, {\"url\": \"/customer/\", \"title\": \"客户管理\"}, {\"url\": \"/productcategory/\", \"title\": \"产品分类\"}, {\"url\": \"/product/\", \"title\": \"产品管理\"}, {\"url\": \"/department/\", \"title\": \"部门管理\"}, {\"url\": \"/service/\", \"title\": \"售后服务\"}, {\"url\": \"/servicedetail/\", \"title\": \"维修服务\"}, {\"url\": \"/contract_file/\", \"title\": \"资料上传\"}, {\"url\": \"/productlabel/\", \"title\": \"产品铭牌\"}, {\"url\": \"/delivery/\", \"title\": \"发货信息\"}, {\"url\": \"/invoice/\", \"title\": \"发票登记\"}]','2026-09-07 03:57:21.274917','2026-09-07 06:38:05.048811'),(4,'upkeeper','售后服务','[\"company_show\", \"delivery_list\", \"department_list\", \"edit_contract_file\", \"electrical_file\", \"get_category_list\", \"get_product_model\", \"get_productcategory_product\", \"get_return_product_model\", \"get_return_product_services\", \"get_servicedetail_services\", \"load_products\", \"mechanical_file\", \"media\", \"plan_list\", \"product_list\", \"productcategory_list\", \"productlabel_list\", \"return_product_download_excel\", \"return_product_list\", \"search_companys\", \"search_warehouses\", \"service_download_excel\", \"service_edit\", \"service_list\", \"servicedetail_add\", \"servicedetail_delete\", \"servicedetail_download_excel\", \"servicedetail_edit\", \"servicedetail_list\", \"task_list\", \"upload_excel\", \"user_add\", \"user_edit\", \"user_list\", \"user_reset\", \"warehouse_list\"]','[{\"url\": \"/plan/\", \"title\": \"生产计划\"}, {\"url\": \"/contract_file/\", \"title\": \"资料上传\"}, {\"url\": \"/task/\", \"title\": \"派任务单\"}, {\"url\": \"/productlabel/\", \"title\": \"产品铭牌\"}, {\"url\": \"/delivery/\", \"title\": \"入库发货\"}, {\"url\": \"/warehouse/\", \"title\": \"仓库管理\"}, {\"url\": \"/department/\", \"title\": \"部门管理\"}, {\"url\": \"/customer/\", \"title\": \"客户管理\"}, {\"url\": \"/productcategory/\", \"title\": \"产品分类\"}, {\"url\": \"/product/\", \"title\": \"产品管理\"}, {\"url\": \"/service/\", \"title\": \"售后服务\"}, {\"url\": \"/servicedetail/\", \"title\": \"维修服务\"}, {\"url\": \"/return_product/\", \"title\": \"售后返件\"}, {\"url\": \"/company/\", \"title\": \"公司信息\"}]','2026-09-07 03:57:21.373645','2026-09-09 01:11:56.001906'),(5,'finance','财务经理','[\"category_list\", \"collection_list\", \"contract_file\", \"contract_file_list\", \"contract_list\", \"contract_product\", \"customer_list\", \"delivery_list\", \"department_list\", \"edit_contract_file\", \"get_invoice_contracts\", \"invoice_add\", \"invoice_delete\", \"invoice_edit\", \"invoice_list\", \"load_products\", \"plan_list\", \"product_list\", \"productcategory_list\", \"productlabel_list\", \"search_companys\", \"search_warehouses\", \"user_list\", \"warehouse_list\"]','[{\"url\": \"/contract/\", \"title\": \"合同管理\"}, {\"url\": \"/collection/\", \"title\": \"回款登记\"}, {\"url\": \"/invoice/\", \"title\": \"发票登记\"}, {\"url\": \"/plan/\", \"title\": \"生产计划\"}, {\"url\": \"/contract_file/\", \"title\": \"资料上传\"}, {\"url\": \"/task/\", \"title\": \"派任务单\"}, {\"url\": \"/productlabel/\", \"title\": \"产品铭牌\"}, {\"url\": \"/delivery/\", \"title\": \"入库发货\"}, {\"url\": \"/warehouse/\", \"title\": \"仓库管理\"}, {\"url\": \"/department/\", \"title\": \"部门管理\"}, {\"url\": \"/user/\", \"title\": \"用户管理\"}, {\"url\": \"/customer/\", \"title\": \"客户管理\"}, {\"url\": \"/productcategory/\", \"title\": \"产品分类\"}, {\"url\": \"/product/\", \"title\": \"产品管理\"}, {\"url\": \"/service/\", \"title\": \"售后服务\"}, {\"url\": \"/servicedetail/\", \"title\": \"维修服务\"}, {\"url\": \"/return_product/\", \"title\": \"售后返件\"}, {\"url\": \"/chart/\", \"title\": \"数据统计\"}, {\"url\": \"/database/backup/\", \"title\": \"数据备份\"}, {\"url\": \"/log/\", \"title\": \"操作日志\"}, {\"url\": \"/company/\", \"title\": \"公司信息\"}, {\"url\": \"/auth/role/\", \"title\": \"权限管理\"}, {\"url\": \"/delivery/\", \"title\": \"发货信息\"}]','2026-09-07 03:57:21.452598','2026-09-07 04:06:16.637564');
/*!40000 ALTER TABLE `auth_role` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_profile`
--

DROP TABLE IF EXISTS `auth_user_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_profile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `extra_permissions` json NOT NULL,
  `denied_permissions` json NOT NULL,
  `menus` json NOT NULL,
  `menu_customize` tinyint(1) NOT NULL,
  `update_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `auth_user_profile_user_id_f9aded29_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_profile`
--

LOCK TABLES `auth_user_profile` WRITE;
/*!40000 ALTER TABLE `auth_user_profile` DISABLE KEYS */;
INSERT INTO `auth_user_profile` VALUES (1,20,'[]','[]','[]',0,'2026-09-09 01:04:28.080098'),(2,1,'[]','[]','[]',0,'2026-09-11 06:49:22.561435');
/*!40000 ALTER TABLE `auth_user_profile` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-22  9:34:35

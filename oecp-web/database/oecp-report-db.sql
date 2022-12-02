/*
 Navicat Premium Data Transfer

 Source Server         : raspi
 Source Server Type    : MySQL
 Source Server Version : 80030
 Source Host           : 192.168.1.7:3306
 Source Schema         : oecp

 Target Server Type    : MySQL
 Target Server Version : 80030
 File Encoding         : 65001

 Date: 28/10/2022 17:24:24
*/

SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for abi_differences_compare
-- ----------------------------
DROP TABLE IF EXISTS `abi_differences_compare`;
CREATE TABLE `abi_differences_compare`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `rpm_package` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `source` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_result` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `category_level` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `effect_drivers` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `detail_path` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `report_base_id` int(0) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1605443 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for all_result_report
-- ----------------------------
DROP TABLE IF EXISTS `all_result_report`;
CREATE TABLE `all_result_report`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `report_base_id` int(0) NULL DEFAULT NULL,
  `category` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `same` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `diff` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `less` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `more` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 26 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for all_rpm_report
-- ----------------------------
DROP TABLE IF EXISTS `all_rpm_report`;
CREATE TABLE `all_rpm_report`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `source_binary_rpm_package` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `source_src_package` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_binary_rpm_package` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_src_package` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_result` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `category_level` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `more` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `less` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `diff` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `report_base_id` int(0) NOT NULL,
  `compare_detail` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `same` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 142348 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for diff_service_detail
-- ----------------------------
DROP TABLE IF EXISTS `diff_service_detail`;
CREATE TABLE `diff_service_detail`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `report_base_id` int(0) NOT NULL,
  `rpm_package` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `source` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_result` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `file_name` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `detail_path` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 480161 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for interface_change
-- ----------------------------
DROP TABLE IF EXISTS `interface_change`;
CREATE TABLE `interface_change`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `report_base_id` int(0) NULL DEFAULT NULL,
  `interface_change` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `interface_add` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `interface_del` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `param_change` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `struct_change` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `struct_del` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `struct_add` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `level` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for kernel
-- ----------------------------
DROP TABLE IF EXISTS `kernel`;
CREATE TABLE `kernel`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `report_base_id` int(0) NULL DEFAULT NULL,
  `kernel_analyse` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `more` int(0) NULL DEFAULT NULL,
  `less` int(0) NULL DEFAULT NULL,
  `same` int(0) NULL DEFAULT NULL,
  `diff` int(0) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 37 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for md_detail
-- ----------------------------
DROP TABLE IF EXISTS `md_detail`;
CREATE TABLE `md_detail`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `report_base_id` int(0) NOT NULL,
  `detail_path` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `md_content` longtext CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 170411 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for osv_technical_report
-- ----------------------------
DROP TABLE IF EXISTS `osv_technical_report`;
CREATE TABLE `osv_technical_report`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `report_base_id` int(0) NULL DEFAULT NULL,
  `osv_version` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `architecture` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `release_addr` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `checksum` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `base_home_old_ver` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `detection_result` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `detail_json` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 14 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for report_base
-- ----------------------------
DROP TABLE IF EXISTS `report_base`;
CREATE TABLE `report_base`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `title` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `source_version` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `target_version` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `state` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `create_time` datetime(0) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 17 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for report_change_info
-- ----------------------------
DROP TABLE IF EXISTS `report_change_info`;
CREATE TABLE `report_change_info`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `report_base_id` int(0) NULL DEFAULT NULL,
  `r_delete` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `r_add` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `r_release` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `version_update` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `consistent` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `provide_change` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `require_change` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `level` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 28 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for report_detail_base
-- ----------------------------
DROP TABLE IF EXISTS `report_detail_base`;
CREATE TABLE `report_detail_base`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `rpm_package` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `source` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_result` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `category_level` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `effect_drivers` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `md_detail_path` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `detail_path` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `report_base_id` int(0) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3813646 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for rpm_requires_analyse
-- ----------------------------
DROP TABLE IF EXISTS `rpm_requires_analyse`;
CREATE TABLE `rpm_requires_analyse`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `report_base_id` int(0) NULL DEFAULT NULL,
  `rpm_package` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `source_symbol_name` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL,
  `source_package` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL,
  `source_dependence_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_symbol_name` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL,
  `compare_package` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL,
  `compare_dependence_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_result` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `compare_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `detail_path` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `category_level` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 407701 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for rpmfile_analyse
-- ----------------------------
DROP TABLE IF EXISTS `rpmfile_analyse`;
CREATE TABLE `rpmfile_analyse`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `rpm_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `rpm_level` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `report_base_id` int(0) NULL DEFAULT NULL,
  `package_change` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `file_more` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `file_less` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `file_consistent` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `file_content_change` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 190 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for service_cmd_conf
-- ----------------------------
DROP TABLE IF EXISTS `service_cmd_conf`;
CREATE TABLE `service_cmd_conf`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `report_base_id` int(0) NULL DEFAULT NULL,
  `service_rpm_change` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `service_file_add` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `service_file_less` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `service_file` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `service_file_name` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `service_file_path` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `cmd_rpm_change` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `cmd_file_add` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `cmd_file_less` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `cmd_file` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `cmd_file_name` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `cmd_file_path` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `conf_rpm_change` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `conf_file_add` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `conf_file_less` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `conf_file` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `conf_file_name` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `conf_file_path` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `level` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Procedure structure for clean_error_report
-- ----------------------------
DROP PROCEDURE IF EXISTS `clean_error_report`;
delimiter ;;
CREATE PROCEDURE `clean_error_report`(IN `report_base_id` int)
BEGIN
	delete from osv_technical_report where osv_technical_report.report_base_id=`report_base_id`;
	delete from abi_differences_compare where abi_differences_compare.report_base_id=`report_base_id`;
	delete from all_rpm_report where all_rpm_report.report_base_id=`report_base_id`;
	delete from interface_change where interface_change.report_base_id=`report_base_id`;
	delete from report_change_info where report_change_info.report_base_id=`report_base_id`;
	delete from report_detail_base where report_detail_base.report_base_id=`report_base_id`;
	delete from service_cmd_conf where service_cmd_conf.report_base_id=`report_base_id`;
	delete from report_base where report_base.id=`report_base_id`;
	delete from rpmfile_analyse where rpmfile_analyse.report_base_id=`report_base_id`;
	delete from kernel where kernel.report_base_id=`report_base_id`;
	delete from md_detail where md_detail.report_base_id=`report_base_id`;
	delete from diff_service_detail where diff_service_detail.report_base_id=`report_base_id`;
	delete from rpm_requires_analyse where rpm_requires_analyse.report_base_id=`report_base_id`;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for compare_report_change_info
-- ----------------------------
DROP PROCEDURE IF EXISTS `compare_report_change_info`;
delimiter ;;
CREATE PROCEDURE `compare_report_change_info`(IN `p_report_base_id` INT)
BEGIN
	DECLARE p_r_add int DEFAULT 0;
	DECLARE p_r_delete int DEFAULT 0;
	DECLARE p_r_release int DEFAULT 0;
	DECLARE p_version_update int DEFAULT 0;
	DECLARE p_r_consistent int DEFAULT 0;
	DECLARE p_provide_change int DEFAULT 0;
	DECLARE p_require_change int DEFAULT 0;
	DECLARE p_r_level VARCHAR(20) DEFAULT 'ALL';
	
	-- ------------------------------------------ALL------------------------------------------------------
	-- 新增
	select count(1) INTO p_r_add  from all_rpm_report where report_base_id=`p_report_base_id` and compare_type='rpm package name' and compare_result=5 ;
	-- 删除
	select count(1) INTO  p_r_delete from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and compare_result=4 ;
	-- release
	select count(1) INTO p_r_release  from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and compare_result=2 ;
	-- 版本升级
	select count(1) INTO p_version_update   from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and compare_result=3 ;
	-- 保持一致
	select count(1) INTO p_r_consistent  from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and (compare_result='same' or compare_result=1 or compare_result=1.1);
	-- provide变化
	select count(1) INTO p_provide_change  from all_rpm_report where report_base_id=`p_report_base_id` and compare_result='diff' and compare_type='rpm provides' ;
	-- require变化
	select count(1) INTO p_require_change from all_rpm_report where report_base_id=`p_report_base_id` and compare_result='diff' and compare_type='rpm requires' ;
	
	-- 插入数据
	INSERT INTO `report_change_info` (report_base_id,r_delete,r_add,r_release,version_update,consistent,provide_change,require_change,level)
	VALUES (`p_report_base_id`,p_r_delete,p_r_add,p_r_release,p_version_update,p_r_consistent,p_provide_change,p_require_change,p_r_level);
	
	
	-- ------------------------------------------L1------------------------------------------------------
	-- 新增
	select count(1) INTO p_r_add  from all_rpm_report where report_base_id=`p_report_base_id` and compare_type='rpm package name' and compare_result=5 and category_level=1;
	-- 删除
	select count(1) INTO  p_r_delete from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and compare_result=4 and category_level=1;
	-- release
	select count(1) INTO p_r_release  from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and compare_result=2 and category_level=1;
	-- 版本升级
	select count(1) INTO p_version_update   from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and compare_result=3 and category_level=1;
	-- 保持一致
	select count(1) INTO p_r_consistent  from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and (compare_result='same' or compare_result=1 or compare_result=1.1) and category_level=1;
	-- provide变化
	select count(1) INTO p_provide_change  from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm provides' and compare_result='diff' and category_level=1;
	-- require变化
	select count(1) INTO p_require_change from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm requires' and compare_result='diff' and category_level=1;
	
	SET p_r_level = 'L1';
	-- 插入数据
	INSERT INTO `report_change_info` (report_base_id,r_delete,r_add,r_release,version_update,consistent,provide_change,require_change,level)
	VALUES (`p_report_base_id`,p_r_delete,p_r_add,p_r_release,p_version_update,p_r_consistent,p_provide_change,p_require_change,p_r_level);
	
	
	-- ------------------------------------------L2------------------------------------------------------
	-- 新增
	select count(1) INTO p_r_add  from all_rpm_report where report_base_id=`p_report_base_id` and compare_type='rpm package name' and compare_result=5 and category_level=2;
	-- 删除
	select count(1) INTO  p_r_delete from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and compare_result=4 and category_level=2;
	-- release
	select count(1) INTO p_r_release  from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and compare_result=2 and category_level=2;
	-- 版本升级
	select count(1) INTO p_version_update   from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and compare_result=3 and category_level=2;
	-- 保持一致
	select count(1) INTO p_r_consistent  from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm package name' and (compare_result='same' or compare_result=1 or compare_result=1.1) and category_level=2;
	-- provide变化
	select count(1) INTO p_provide_change  from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm provides' and compare_result='diff' and category_level=2;
	-- require变化
	select count(1) INTO p_require_change from all_rpm_report where report_base_id=`p_report_base_id` and  compare_type='rpm requires' and compare_result='diff' and category_level=2;
	
	SET p_r_level = 'L2';
	-- 插入数据
	INSERT INTO `report_change_info` (report_base_id,r_delete,r_add,r_release,version_update,consistent,provide_change,require_change,level)
	VALUES (`p_report_base_id`,p_r_delete,p_r_add,p_r_release,p_version_update,p_r_consistent,p_provide_change,p_require_change,p_r_level);

END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;

## 0. 背景说明

工具聚焦openEuler内核和基础包，检测伙伴二次发行版生态核心特性不丢失，关键配置不更改 结合社区选包策略及软件包等级策略，检查L1、L2软件包版本、打包方式、接口一致性，KABI白名单，架构特性(如鲲鹏/X86特性)使能，性能优化配置，牵引实现扩展仓库openEuler系共享、共用，主流行业应用在openEuler系不同的OSV生态复用度95%。

检查项

| 序号 | 检查                   |
| ---- | ---------------------- |
| 1    | 软件包检测             |
| 2    | 特性检测               |
| 3    | 配置检测               |

验证项

| 序号 | 验证项       | 测试                   |
| ---- | ------------ | ---------------------- |
| 1    | 兼容性测试   | 安装、卸载、命令、服务 |
| 2    | 基础性能测试 | 基础benchmark 测试     |
| 3    | 特性测试     | 特性功能验证           |
| 4    | 功能测试     | 基础AT测试             |


## 1. 运行环境

### 1.1. oecp运行环境依赖组件

| 组件      | 组件描述                                                     | 可获得性                                             |
| --------- | ------------------------------------------------------------ | ---------------------------------------------------- |
| python3   | python3.7.9及以上| 可先通过yum list命令查看，如果没有该版本需要下载安装 |
| sqlite    | v3.7.17 及以上版本                                           | 系统自带                                             |

### 1.2. oecp理论运行资源

在运行oecp分析之前，确保虚拟机或物理机的运行规格**大于等于2U8G**，运行前建议重启虚拟机，保证空闲内存足够，建议oecp所在目录空闲磁盘至少**保留20GB**（具体以实际扫描rpm包数量为准）

| 任务分析项           | CPU资源消耗     | 运行耗时                                                          | 输出件大小                                                                        |
| -------------------- | --------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| 比较两个iso镜像所有比较计划| 2核心，峰值100% | 20~60分钟|程序正常结束，百兆级别，具体大小和比较的镜像差异有关|
| 比较两个iso镜像所有比较计划| 16核心，峰值100% | 10~60分钟|程序正常结束，百兆级别，具体大小和比较的镜像差异有关|

### 1.3. oecp网络需求

除了相关组件安装，oecp**可完全离线运行**，无需连接网络

## 2. 软件目录结构

| 主目录      | 二级目录               | 三级目录                    | 描述              |
| ----------- | ---------------------- |-------------------------|-----------------|
| cli.py      |                        |                         | 命令启动脚本          |
| requirement |                        |                         | 工具依赖清单          |
| README.md   |                        |                         | 用户指导手册          |
| test        |                        |                         | 测试脚本文件夹           |
| doc         |                        |                         | 设计文档文件夹         |
|             | oecpimg                |                         | 存放文档图片          |
|             | oecp-dev-1.0.md        |                         | 设计文档            |
|             | oecp-module-dev-1.0.md |                         | 模块设计文档          |
| oecp        |                        |                         |                 |
|             | main                   |                         | 主模块             |
|             |                        | factory.py              | 工厂方法，生产ISO、REPO等比较对象 |
|             |                        | directory.py            | 目录级别对象、ISO对象、REPO对象 |
|             |                        | repository.py           | 仓库级别对象          |
|             |                        | mapping                 | 二进制包和源码包映射      |
|             |                        | category.py             | 软件包、二进制包等级      |
|             |                        | plan.py                 | 比较计划            |
|             | executor               |                         | 比较模块            |
|             |                        | base.py                 | 比较器基类           |
|             |                        | list.py                 | 比较文件列表、包列表      |
|             |                        | null.py                 | 空比较，当比较计划项只需要dumper时使用 |
|             |                        | nvs.py                  | 符号、版本、名称比较器     |
|             |                        | plain.py                | 配置文件比较          |
|             |                        | abi.py                  | 比较abi           |
|             |                        | cmd.py                  | 比较命令文件、库文件      |
|             |                        | header.py               | 比较头文件           |
|             |                        | service.py              | 比较服务文件          |
|             | dumper                 |                         | dumper模块        |
|             |                        | base.py                 | dumper基类        |
|             |                        | config.py               | rpm包的配置文件       |
|             |                        | extract.py              | 提取rpm包内容        |
|             |                        | filelist.py             | 文件列表            |
|             |                        | kconfig.py              | 内核配置            |
|             |                        | kabi.py                 | 内核abi           |
|             |                        | kconfig_drive.py        | 内核驱动配置          |
|             |                        | null.py                 | 当比较计划项只需要执行比较时使用 |
|             |                        | packagelist.py          | ISO中包列表         |
|             |                        | provides.py             | rpm包提供的符号       |
|             |                        | requires.py             | rpm包依赖的符号       |
|             |                        | abi.py                  | rpm包的so库文件      |
|             |                        | cmd.py                  | rpm包的命令文件       |
|             |                        | header.py               | rpm包的头文件        |
|             |                        | service.py              | rpm包的服务文件       |
|             | result                 |                         | 结果模块            |
|             |                        | compare_result.py       | 保存结果对象          |
|             |                        | constants.py            | 比较类型、比较结果宏      |
|             |                        | export.py               | 导出比较结果到csv文件    |
|             |                        | test_result.py          | 导出compass-ci比较的结果 |
|             |                        | json_result.py          | 输出json格式比较结果报告  |
|             |                        | similarity.py           | osv测试关注比较项相似度   |
|             | proxy                  |                         | 第三方代理模块         |
|             |                        | rpm_proxy.py            | rpm包常用方法        |
|             |                        | proxy/requests_proxy.py | requests功能封装下载功能 |
|             | utils                  |                         | 工具模块            |
|             |                        | utils/logger.py         | 日志              |
|             |                        | utils/misc.py           | 常用工具            |
|             |                        | utils/shell.py          | shell命令         |
|             |                        | utils/unit_convert.py   | 单位转换            |
|             | conf                   |                         | 配置模块            |
|             |                        | category                | 包等级配置           |
|             |                        | performance             | compass-ci性能测试  |
|             |                        | plan                    | 比较计划            |
|             |                        | logger.conf             | 日志配置            |

## 3. 主要功能介绍

oecp工具适用于比较两个ISO镜像之间的差别，具体比较项有：

1）仓库rpm的packagelist（两个仓库包名、版本号、release号比较），对应报告比较类型如下：

- rpm package name
- rpm filelist

2）config（rpm包内配置）、kconfig（内核配置文件），对应报告比较类型如下：

- rpm config
- rpm kconfig

3）provides（rpm的provides）、requires（rpm的依赖）等, 对应报告比较类型如下：

- rpm provides
- rpm requires

4）unixbench, lmbench, mysql性能测试，对应报告比较类型如下：

- performacne

5）服务命令起停测试，对应报告比较类型如下：

- rpm test


## 4. oecp下载安装与部署

install oecp:
'''
git clone https://gitee.com/openeuler/oecp
cd oecp
pip3 install -r requirement
'''

## 5. oecp使用
使用前，安装python依赖库
pip3 install -r requirement

`python3 cli.py [-h] [-n PARALLEL] [-w WORK_DIR] [-p PLAN_PATH]
                [-c CATEGORY_PATH] [--platform PLATFORM_TEST_PATH]
                [-f OUTPUT_FORMAT] [-o OUTPUT_FILE] [-d DEBUGINFO]
                file1 file2`
* **位置参数(必选)**
  * **`file`**
    指定两个比较的iso文件/存放rpm包的目录（directory）/rpm包，以file1作为基准

* **可选参数**

  * **`-n, --parallel`**
    指定`进程池并发数量`，默认cpu核数

  * **`-w, --work-dir`**
    指定`工作路径`，默认路径为/tmp/oecp
  
  * **`-p, --plan`**
    指定`比较计划`，默认为oecp/conf/plan/all.json

  * **`-c, --category`**
    指定`包级别信息`，默认为oecp/conf/category/category.json
  
  * **`-f, --format`**
    指定`输出格式`，默认为csv

  * **`-o, --output`**
    指定`输出结果路径`，默认为/tmp/oecp
  
  * **`-d, --debuginfo`**
    指定`debuginfo iso/rpm路径`

  * **`--platform`**
    指定`进行平台验证有关json报告地址`，默认为/tmp/oecp；性能测试默认基线文件为oecp/conf/performance/openEuler-20.03-LTS-aarch64-dvd.iso.performance.json
    
  * **举例**

    * **` python3 cli.py  /root/openEuler-20.03-LTS-aarch64-dvd.iso /root/openEuler-20.03-LTS-SP1-aarch64-dvd.iso`**

  * **比较计划说明**
    * **`all.json`**
      涵盖下面所有配置项的比较
    * **`config_file.json`**
      比较rpm包中配置文件内容的差异，需依赖RPMExtractDumper（提取解压rpm的dumper类）
    * **`filelist.json`**
      比较rpm包文件列表差异，可通过rpm -pql ${rpm_path}命令获取rpm文件列表
    * **`kconfig.json`**
      比较内核配置文件，需依赖RPMExtractDumper（提取解压rpm的dumper类）
    * **`package_list.json`**
      比较两个rpm集合包名称、版本、发行版本的差异
    * **`provides_requires.json`**
      比较rpm的provides和requires差异，可通过rpm -pq --provides/requires ${rpm_path}查询

## 6.  软件卸载与环境清理

## 7.  OECP报告说明

 1）最终报告

oecp工具会展示一份最终报告，用于展示最终的测试结果，测试结果参考osv测试标准。

 2）报告目录结构

| 主目录               | 二级目录                      | 三级目录               | 文件内容描述           |
|-------------------|-------------------------------|--------------------|------------------|
| report-iso-a--iso-b |                               |                    | 最终报告目录名称         |
|                   | kernel_analyse                |                    | 内核比较结果目录         |
|                   |                               | drive-kabi         | 内核驱动abi比较结果目录    |
|                   |                               | drive-kconfig      | 内核驱动配置比较结果目录     |
|                   |                               | kabi               | 内核abi比较结果目录      |
|                   |                               | kconfig            | 内核配置比较结果目录       |
|                   | rpm_analyse                   |                    | rpm比较结果目录        |
|                   |                               | rpm-provides       | rpm包提供符号比较结果目录   |
|                   |                               | rpm-requires       | rpm包依赖符号比较结果目录   |
|                   | rpmabi_analyse                |                    | rpm包abi比较结果目录    |
|                   |                               | rpm-abi            | rpm abi比较结果目录    |
|                   | rpmfile_analyse               |                    | rpm包文件比较结果目录     |
|                   |                               | rpm-cmd            | rpm包命令文件比较结果目录   |
|                   |                               | rpm-config         | rpm包配置文件比较结果目录   |
|                   |                               | rpm-files          | rpm包其他类型文件比较结果目录 |
|                   |                               | rpm-header         | rpm包头文件比较结果目录    |
|                   |                               | rpm-lib            | rpm包so库文件比较结果目录  |
|                   |                               | rpm-service        | rpm包服务文件比较结果目录   |
|                   | rpm-test                      |                    | 测试repo中所有rpm安装结果目录 |
|                   | details_analyse               |                    | rpm文件比较内容目录      |
|                   |                               | abi                | so库文件接口变化详情      |
|                   |                               | config             | 配置文件内容变化详情       |
|                   |                               | header             | 头文件内容变化详情        |
|                   |                               | service-detail     | 服务文件配置变化详情       |
|                   | all-AT-report.csv             |                    | 社区AT用例运行测试结果     |
|                   | all-ciconfig-report.csv       |                    | OSV版本运行时默认配置一致性结果 |
|                   | all-ci-file-config-report.csv |                    | 运行时默认配置文件一致性结果   |
|                   | all-differences-report.csv    |                    | 静态检测所有比较差异结果汇总展示 |
|                   | all-performance-report.csv    |                    | 基础性能测试统计结果       |
|                   | all-rpm-report.csv            |                    | 静态检测rpm包层面比较结果汇总 |
|                   | all-result-report.csv         |                    | rpm包等级比较结果统计     |
|                   | all-rpm-test-report.csv       |                    | rpm安装平台测试结果统计    |
|                   | all-similarity-report.csv     |                    | osv测试关注比较项相似度统计  |
|                   | osv_data_summary.xlsx         |                    | osv测评报告          |
|                   | similar_calculate_result.csv  |                    | 软件包测试项结果统计       |
|                   | similar_calculate_result.csv  |                    | 软件包测试项结果统计       |
|                   | web_show_result.json          |                    | osv测评json报告      |

  输出比较结果报告中内容可分为*静态检测报告*及*平台验证分析报告*，报告文件数量取决于比较内容，此目录展示所有比较报告完全生成场景。

 3）all-rpm-report报告结果参数解析

  该报告用于暂时保存rpm对比的详细结果：

  compare type栏显示为比较规则，其中包名比较规则如下：

  Explain for rpm package name compare result:

                    1   -- same name + version + release num + distributor

                    1.1 -- same name + version + release num

                    2   -- same name + version

                    3   -- same name

                    4   -- less

                    5   -- more

    其中1 ，1.1 ，2在最后计算的时候都会作为same比较

    此报告中单项比较结果可以根据compare detail下的路径，去查看该比较项对应各层文件夹中的详细报告

  Explain for rpm category level:

                level 0   --  核心包等级

                level 1   --  软件包及软件包 API、ABI 在某个 LTS 版本的生命周期保持不变，跨 LTS 版本不保证

                level 2   --  软件包及软件包 API、ABI 在某个 SP 版本的生命周期保持不变，跨 SP 版本不保证

                level 3   --  版本升级兼容性不做保证

                level 4   --  未指定的软件包
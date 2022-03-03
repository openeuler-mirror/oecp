## 0. 工具说明

社区网站发布通过OSV认证的厂商及版本号，对外价值 — 确保根生态一致性，核心特性继承，生态可复用；对内价值 — 反生态分裂识别，保障技术路线演进，OSV认证方案：聚焦openEuler内核和基础包，约束伙伴二次发行版生态核心特性不丢失，关键配置不更改

**Compatible深度：主力行业场景生态复用（通用OSV）**

在Compatible 基础基础上，检测生态复用，扩展竞争力特性(etmem、热升级、isulad)继承检测；扩展标准包到L2包一致性，主流行业应用生态复用度90%。检查发行版是否结合社区选包策略及软件包等级策略，检查L1、L2软件包版本、打包方式、接口一致性，实现扩展仓库openEuler系共享、共用。

**Compatible基础：特性/配置继承 (企业OSV)**

主要检测openEuler 技术路线，是否有反分裂行为，核心包L1(内核、glibc)及包管理体系一致性，KABI白名单，架构特性(如鲲鹏/X86特性)使能，性能优化配置。检查发行版是否技术路线一致，是否有反分裂行为，核心包一致性，如支持鲲鹏补丁、X86补丁、isulad、热升级等特性合入，充分发挥openEuler竞争力特性。

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

| 主目录      | 二级目录               | 三级目录                | 描述                                   |
| ----------- | ---------------------- | ----------------------- | -------------------------------------- |
| cli.py      |                        |                         | 命令启动脚本                           |
| requirement |                        |                         | 工具依赖清单                           |
| README.md   |                        |                         | 用户指导手册                           |
| test        |                        |                         | 测试脚本夹                             |
| doc         |                        |                         | 设计文档文件夹                         |
|             | oecpimg                |                         | 存放文档图片                           |
|             | oecp-dev-1.0.md        |                         | 设计文档                               |
|             | oecp-module-dev-1.0.md |                         | 模块设计文档                           |
| oecp        |                        |                         |                                        |
|             | main                   |                         | 主模块                                 |
|             |                        | factory.py              | 工厂方法，生产ISO、REPO等比较对象      |
|             |                        | directory.py            | 目录级别对象、ISO对象、REPO对象        |
|             |                        | repository.py           | 仓库级别对象                           |
|             |                        | mapping                 | 二进制包和源码包映射                   |
|             |                        | category.py             | 软件包、二进制包等级                   |
|             |                        | plan.py                 | 比较计划                               |
|             | executor               |                         | 比较模块                               |
|             |                        | base.py                 | 比较器基类                             |
|             |                        | list.py                 | 比较文件列表、包列表                   |
|             |                        | null.py                 | 空比较，当比较计划项只需要dumper时使用 |
|             |                        | nvs.py                  | 符号、版本、名称比较器                 |
|             |                        | plain.py                | 文件比较                               |
|             | dumper                 |                         | dumper模块                             |
|             |                        | base.py                 | dumper基类                             |
|             |                        | config.py               | rpm包的配置文件                        |
|             |                        | extract.py              | 提取rpm包内容                          |
|             |                        | filelist.py             | 文件列表                               |
|             |                        | kconfig.py              | 内核配置                               |
|             |                        | null.py                 | 当比较计划项只需要执行比较时使用       |
|             |                        | packagelist.py          | ISO中包列表                            |
|             |                        | provides.py             | rpm包提供的符号                        |
|             |                        | requires.py             | rpm包依赖的符号                        |
|             | result                 |                         | 结果模块                               |
|             |                        | compare_result.py       | 保存结果对象                           |
|             |                        | constants.py            | 比较类型、比较结果宏                   |
|             |                        | export.py               | 导出比较结果到csv文件                  |
|             |                        | test_result.py          | 导出compass-ci比较的结果               |
|             | proxy                  |                         | 第三方代理模块                         |
|             |                        | rpm_proxy.py            | rpm包常用方法                          |
|             |                        | proxy/requests_proxy.py | requests功能封装下载功能               |
|             | utils                  |                         | 工具模块                               |
|             |                        | utils/logger.py         | 日志                                   |
|             |                        | utils/misc.py           | 常用工具                               |
|             |                        | utils/shell.py          | shell命令                              |
|             |                        | utils/unit_convert.py   | 单位转换                               |
|             | conf                   |                         | 配置模块                               |
|             |                        | category                | 包等级配置                             |
|             |                        | performance             | compass-ci性能测试                     |
|             |                        | plan                    | 比较计划                               |
|             |                        | logger.conf             | 日志配置                               |

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
git clone https://gitee.com/xielihao/oecp-lite.git
cd oecp
pip3 install -r requirement
'''

## 5. oecp使用
使用前，安装python依赖库
pip3 install -r requirement

`python3 cli.py [-h] [-n PARALLEL] [-w WORK_DIR] [-p PLAN_PATH]
                [-c CATEGORY_PATH] [-b PERF_BASELINE_FILE] [-a {x86_64,aarch64}]
                [-f OUTPUT_FORMAT] [-o OUTPUT_FILE]
                file1 file2`
* **位置参数(必选)**
  * **`file`**
    指定两个比较的iso文件

* **可选参数**

  * **`-n, --parallel`**
    指定`进程池并发数量`，默认cpu核数

  * **`-w, --work-dir`**
    指定`工作路径`，默认路径为/tmp/oecp
  
  * **`-p, --plan`**
    指定`比较计划`，默认为oecp/conf/plan/all.json

  * **`-c, --category`**
    指定`包级别信息`，默认为oecp/conf/category/category.json

  * **`-b, --baseline`**
    指定`基线文件`，默认为oecp/conf/performance/openEuler-20.03-LTS-aarch64-dvd.iso.performance.json


  * **`-f, --format`**
    指定`输出格式`，默认为csv

  * **`-o, --output`**
    指定`输出结果路径`，默认为/tmp/oecp
    
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

##### 1.最终报告

OECP最终报告解读参见OECP测试标准

##### 2.all-similarity-report

该报告展示了osv测试数据的汇总，有些数据目前暂时不用于最终比较

##### 3.all-rpm-test-report

该报告用于展示测试repo安装的时候，rpm包安装的结果

##### 4.all-result-report

该报告用于展示rpm包对比的汇总结果

##### 5.all-rpm-report

该报告用于暂时rpm对比的详细结果：

compare type栏显示为比较规则，其中包名比较规则如下：

rpm package name explan:
                    1   -- same name + version + release num + 包名后缀

                    1.1 -- same name + version + release num

                    2   -- same name + version

                    3   -- same name

                    4   -- less

                    5   -- more

其中，1 ，1.1 ，2在最后计算的时候都会作为same比较

可以根据compare detail下的路径，去结果的各层文件夹中取找到详细的报告

##### 6.all-pergormance-report

性能数据统计
# 1、需求描述
工具聚焦openEuler内核和基础包，检测伙伴二次发行版生态核心特性不丢失，关键配置不更改 结合社区选包策略及软件包等级策略，检查L1、L2软件包版本、打包方式、接口一致性，KABI白名单，架构特性（如ARM/X86特性）使能，性能优化配置，牵引实现扩展仓库openEuler系共享、共用，主流行业应用在openEuler系不同的OSV生态复用度。级等特性合入，充分发挥openEuler竞争力特性。

**检查项**

| 序号 | 检查                   |
| ---- | ---------------------- |
| 1    | 软件包检测             |
| 2    | 接口检测               |
| 3    | 特性检测               |
| 4    | 配置检测               |
| 5    | 补丁检测(需要依赖源码) |

**验证项**

| 序号 | 验证项       | 测试                   |
| ---- | ------------ | ---------------------- |
| 1    | 兼容性测试   | 安装、卸载、命令、服务 |
| 2    | 基础性能测试 | 基础benchmark 测试     |
| 3    | 特性测试     | 特性功能验证           |
| 4    | 功能测试     | 基础AT测试             |

## 1.1、受益人
_围绕特性价值，该特性实现后给哪些角色带来益处，哪些角色会使用_
| 角色 | 角色描述 |
| :--- | :------- |
|      |          |
|      |          |

## 1.3、依赖组件
| 组件                    | 组件描述           | 可获得性                                                     |
| ----------------------- | ------------------ | ------------------------------------------------------------ |
| python3                 | python3.7.9及以上  | 可先通过yum list命令查看，如果没有该版本需要下载安装         |
| sqlite                  | v3.7.17 及以上版本 | 系统自带                                                     |
| abidiff                 | 1.6.0              | 挂载openEuler20.03-LTS-SP2的yum源之后，yum install libabigail |
| japi-compliance-checker | 2.4                | https://github.com/lvc/japi-compliance-checker               |
| createrepo              | -                  | yum install -y createrepo                                  |
| binutils                | -                  | yum install -y binutils                                    |

## 1.3、License

Mulan V2

## 1.4、需求清单

### 1.4.1、工具需求规格项

### 1.4.2、工具交互需求

### 1.4.3、工具检测能力项

### 1.4.4、工具展示项

### 1.4.5、工具验证用例项

# 2、设计概述

## 2.1、分析思路

## 2.2、设计原则

- 数据与代码分离： 功能实现是需要考虑哪些数据是需要配置动态改变的，不可在代码中将数据写死，应提取出来做成可配置项。

- 分层原则： 上层业务模块的数据查询应通过查询模块调用数据库获取数据，不可直接跨层访问数据库。

- 接口与实现分离：外部依赖模块接口而不是依赖模块实现。

- 模块划分： 模块之间只能单向调用，不能存在循环依赖。

- 变更： 架构设计变更、外部接口变更、特性需求变更需要结合开发、测试等所有相关人员经过开会讨论后决策，不可擅自变更。

# 3、需求分析
## 3.1、USE-CASE视图

![输入图片说明](https://foruda.gitee.com/images/1676024048189491803/37cb46e9_9520150.jpeg "用例视图.jpg")

## 3.2、工具上下文


![输入图片说明](https://foruda.gitee.com/images/1676023190104218922/7ae8654f_9520150.jpeg "工具上下文.jpg")
## 3.3、逻辑视图


![输入图片说明](https://foruda.gitee.com/images/1676023170691857145/e0f9c5f8_9520150.jpeg "逻辑模型.jpg")



## 3.4、开发视图


| 主目录      | 二级目录               | 三级目录                    | 描述                     |
| ----------- | ---------------------- |-------------------------|------------------------|
| cli.py      |                        |                         | 命令启动脚本                 |
| requirement |                        |                         | 工具依赖清单                 |
| README.md   |                        |                         | 用户指导手册                 |
| test        |                        |                         | 测试脚本夹                  |
| doc         |                        |                         | 设计文档文件夹                |
|             | oecpimg                |                         | 存放文档图片                 |
|             | oecp-dev-1.0.md        |                         | 设计文档                   |
|             | oecp工具报告说明.md     |                         | 输出csv格式报告说明解析          |
|             | oecp工具检测标准.md     |                         | 工具检测标准说明               |
|             | oecp-module-dev-1.0.md |                         | 模块设计文档                 |
| oecp        |                        |                         |                        |
|             | main                   |                         | 主模块                    |
|             |                        | factory.py              | 工厂方法，生产ISO、REPO等比较对象   |
|             |                        | directory.py            | 目录级别对象、ISO对象、REPO对象    |
|             |                        | repository.py           | 仓库级别对象                 |
|             |                        | mapping                 | 二进制包和源码包映射             |
|             |                        | category.py             | 软件包、二进制包等级             |
|             |                        | plan.py                 | 比较计划                   |
|             | executor               |                         | 比较模块                   |
|             |                        | base.py                 | 比较器基类                  |
|             |                        | abi.py                  | abi比较器                 |
|             |                        | lib.py                  | 库文件比较器                 |
|             |                        | cmd.py                  | 命令文件比较器                |
|             |                        | header.py               | 头文件比较器                 |
|             |                        | list.py                 | 比较文件列表、包列表             |
|             |                        | null.py                 | 空比较，当比较计划项只需要dumper时使用 |
|             |                        | nvs.py                  | 符号、版本、名称比较器            |
|             |                        | ko.py                   | 内核模块比较器                |
|             |                        | jabi.py                 | jar包比较器                |
|             |                        | plain.py                | 配置文件比较器                |
|             |                        | service.py              | 服务文件比较器                |
|             | dumper                 |                         | dumper模块               |
|             |                        | base.py                 | dumper基类               |
|             |                        | abi.py                  | 动态/静态库abi              |
|             |                        | config.py               | rpm包的配置文件              |
|             |                        | cmd.py                  | 命令文件                   |
|             |                        | extract.py              | 提取rpm包内容               |
|             |                        | filelist.py             | 文件列表                   |
|             |                        | header.py               | 头文件                    |
|             |                        | jabi.py                 | jar包abi                |
|             |                        | kabi.py                 | 内核abi                  |
|             |                        | ko.py                   | 内核模块                   |
|             |                        | kconfig.py              | 内核配置                   |
|             |                        | kconfig_drive.py        | 内核驱动abi、配置             |
|             |                        | null.py                 | 当比较计划项只需要执行比较时使用       |
|             |                        | packagelist.py          | ISO中包列表                |
|             |                        | provides.py             | rpm包提供的符号              |
|             |                        | requires.py             | rpm包依赖的符号              |
|             |                        | service.py              | 服务文件                   |
|             | result                 |                         | 结果模块                   |
|             |                        | compare_result.py       | 保存结果对象                 |
|             |                        | constants.py            | 比较类型、比较结果宏             |
|             |                        | export.py               | 导出比较结果到csv文件           |
|             |                        | test_result.py          | 导出compass-ci比较的结果      |
|             |                        | json_result.py          | 导出结果为json格式            |
|             |                        | similarity.py           | 检测项结果计算                |
|             |                        | constants.py            | 定义常量                   |
|             |                        | compress.py             | 打包工具输出结果文件             |
|             | proxy                  |                         | 第三方代理模块                |
|             |                        | rpm_proxy.py            | rpm包常用方法               |
|             |                        | proxy/requests_proxy.py | requests功能封装下载功能       |
|             | utils                  |                         | 工具模块                   |
|             |                        | utils/logger.py         | 日志                     |
|             |                        | utils/misc.py           | 常用工具                   |
|             |                        | utils/shell.py          | shell命令                |
|             |                        | utils/unit_convert.py   | 单位转换                   |
|             |                        | utils/kernel.py         | 提取内核目标文件               |
|             |                        | utils/common.py         | 去除重复文件               |
|             | conf                   |                         | 配置模块                   |
|             |                        | category                | 包等级配置                  |
|             |                        | performance             | compass-ci性能测试         |
|             |                        | plan                    | 比较计划                   |
|             |                        | logger.conf             | 日志配置                   |
|             |                        | kabi_whitelist          | 内核白名单                  |
|             |                        | kernel_driver_range     | 内核驱动配置                 |
|             |                        | directory_structure     | 结果目录结构                 |
|             | kabi                   |                         | kabi/kapi基线化功能模块       |
|             |                        | kabi_generate.py        | kabi提取                 |
|             |                        | csv_result.py           | 结果csv文件生成              |
## 3.5、部署视图
_真实环境如何部署，网络和存储如何划分，业务程序如何部署，如何扩展、备份等_

## 3.6、质量属性设计
### 3.6.1、性能规格
在运行oecp分析之前，确保虚拟机或物理机的运行规格**大于等于2U8G**，运行前建议重启虚拟机，保证空闲内存足够，建议oecp所在目录空闲磁盘至少**保留20GB**（具体以实际扫描rpm包数量为准）

| 任务分析项                  | CPU资源消耗      | 运行耗时  | 输出件大小                                           |
| --------------------------- | ---------------- | --------- | ---------------------------------------------------- |
| 比较两个iso镜像所有比较计划 | 2核心，峰值100%  | 20~60分钟 | 程序正常结束，百兆级别，具体大小和比较的镜像差异有关 |
| 比较两个iso镜像所有比较计划 | 16核心，峰值100% | 10~60分钟 | 程序正常结束，百兆级别，具体大小和比较的镜像差异有关 |

### 3.6.2、系统可靠性设计

### 3.6.3、安全性设计

### 3.6.4、兼容性设计

### 3.6.5、可服务性设计

### 3.6.6、可测试性设计

## 3.7、特性清单
| no   | 特性描述 | 代码估计规模 | 实现版本 |
| :--- | :------- | :----------- | :------- |
|      |          |              |          |
|      |          |              |          |

## 3.8、接口清单
### 3.8.1、命令行接口清单


`python3 cli.py [-h] [-n PARALLEL] [-w WORK_DIR] [-p PLAN_PATH]
                [-c CATEGORY_PATH] [--platform PLATFORM_TEST_PATH]
                [-f OUTPUT_FORMAT] [-o OUTPUT_FILE] [-d DEBUGINFO]
                file file`
* **位置参数**
  * **`file`**
    指定两个比较的iso文件/存放rpm包的目录（directory）/rpm包

* **可选参数**

  * **`-n, --parallel`**
    指定`进程池并发数量`，默认cpu核数

  * **`-w, --work-dir`**
    指定`工作路径`，默认路径为/tmp/oecp
  
  * **`-p, --plan`**
    指定`比较计划`

  * **`-c, --category`**
    指定`包级别信息`，默认为src/conf/category/category.json

  * **`--platform`**
    指定`进行平台验证有关json报告地址`，默认为/tmp/oecp；性能测试默认基线文件为oecp/conf/performance/openEuler-20.03-LTS-aarch64-dvd.iso.performance.json

  * **`-f, --format`**
    指定`输出格式`，默认为csv

  * **`-o, --output`**
    指定`输出结果路径`，默认为/tmp/oecp

  * **`-d, --debuginfo`**
    指定`debuginfo iso/rpm路径`
  
  * **`-s, --src_kernel`**
    指定`输入内核源码包路径`，路径下存放内核源码包：kernel-*.src.rpm，比较模式为kapi，需要在对应版本的kernel源码中查找kapi函数原型
  
* **举例**

  * ` python3 cli.py /root/openEuler-20.03-LTS-aarch64-dvd.iso /root/openEuler-20.03-LTS-SP1-aarch64-dvd.iso -p src/conf/plan/test.json`

### 3.8.2、内部模块间接口清单
| 接口名称                                             | 接口描述                                                         | 入参                                                         | 输出                                                                                              | 异常                                                         |
|:-------------------------------------------------|:-------------------------------------------------------------| :----------------------------------------------------------- |:------------------------------------------------------------------------------------------------| :----------------------------------------------------------- |
| `Repository.upsert_a_rpm`                        | 增加一个rpm包                                                     | 工作目录、rpm名、rpm路径、debuginfo包路径                          |                                                                                                 | 无                                                           |
| `Repository.compare`                             | 比较repository                                                 | 比较对手、比较计划                                           | 比较结果对象                                                                                          | 无                                                           |
| `Repository.\__getitem__`                        | 支持遍历所有rpm包                                                   |                                                              | 每一个rpm包描述                                                                                       | 无                                                           |
| `Directory.upsert_a_group`                       | 增加一个子目录                                                      | 子目录路径、debuginfo路径径                    |                                                                                                 | 无                                                           |
| `Directory.compare`                              | 比较目录                                                         | 比较对手、比较计划                                           | 比较结果对象                                                                                          | 无                                                           |
| `DistISO.compare`                                | 比较发布的ISO                                                     | 比较对手、比较计划                                           | 比较结果对象                                                                                          | 无                                                           |
| `OBSRepo`                                        | OBS内部publish的repo                                            |                                                              |                                                                                                 |                                                              |
| `Plan.dumper_of`                                 | 比较项调用的dumper                                                 | 比较项名称                                                   | dumper类对象                                                                                       | 无                                                           |
| `Plan.executor_of`                               | 比较项调用的比较器                                                    | 比较项名称                                                   | 比较器类对象                                                                                          | 无                                                           |
| `Plan.config_of`                                 | 比较项相关的配置                                                     | 比较项名称                                                   | 比较项配置字典                                                                                         | 无                                                           |
| `Plan.only_for_directory`                        | 比较项只针对目录级别对象有效                                               | 比较项名称                                                   | boolean                                                                                         | 无                                                           |
| `Plan.check_specific_package`                    | 比较项只针对特定的包                                                   | 比较项名称、包名                                             | boolean                                                                                         | 无                                                           |
| `Plan.check_specific_category`                   | 比较项只针对特定分类的包                                                 | 比较项名称、分类级别                                         | boolean                                                                                         | 无                                                           |
| `CategoryLevel.level_name_2_enum`                | 包分类级别转换成枚举属性                                                 | 包分类级别名称                                               | 包分类级别枚举属性                                                                                       | 无                                                           |
| `Category.category_of_src_package`               | 获取代码包分类级别                                                    | 包名称                                                       | 分类级别                                                                                            | 无                                                           |
| `Category.category_of_bin_package`               | 获取二进制包分类级别                                                   | 包名称                                                       | 分类级别                                                                                            | 无                                                           |
| `RepositoryPackageMapping.repository_of_package` | 二进制包对应的代码包                                                   | 二进制包名称                                                 | 代码包名称                                                                                           | 无                                                           |
| `RPMProxy.rpm_n_v_r_d_a`                         | 标准二进制包名解析                                                    | 二进制包名称                                                 | 包名、版本、发行号、厂商、架构                                                                                 | 无                                                           |
| `compare_result`                                 | 解析result树中的比较结果，<br>输出scv格式的报告                               | result树，例如：<br>{<br> &nbsp;&nbsp;"cmp_side_a": "openeEuler-20.03-LTS-aarch64-dvd.iso",<br>&nbsp;&nbsp;"cmp_side_b": "openeEuler-20.03-LTS-SP1-aarch64-dvd.iso",<br>&nbsp;&nbsp;"cmp_type": null, <br>&nbsp;&nbsp;"cmp_result": "diff",<br>&nbsp;&nbsp;"diff_components":[<br>&nbsp;&nbsp;&nbsp;&nbsp; repository_result_1,<br>&nbsp;&nbsp;&nbsp;&nbsp; repository_result_2, <br>&nbsp;&nbsp;&nbsp;&nbsp; ...<br>&nbsp;&nbsp;]<br>} | work-dir/report: <br>&nbsp;&nbsp; all-rpm-report.csv, <br>&nbsp;&nbsp; rpm-\*/\*.csv            |                                                              |
| `test_result`                                    | 解析compass-ci测试结果，<br>输出对应csv格式报告                             | compass-ci性能测试结果， 如：<br>&nbsp;&nbsp; work-dir/openeEuler-20.03-LTS-aarch64-dvd.iso.performance.json <br>&nbsp;&nbsp; work-dir/openeEuler-20.03-LTS-SP1-aarch64-dvd.iso.performance.json<br> compass-ci服务命令启停测试结果，如：<br>&nbsp;&nbsp; work-dir/openeEuler-20.03-LTS-aarch64-dvd.iso.tests.json <br>&nbsp;&nbsp; work-dir/openeEuler-20.03-LTS-aarch64-dvd.iso.tests.json | work-dir/report: <br>&nbsp;&nbsp; all-performance-report.csv， <br>&nbsp;&nbsp; rpm-tests/\*.csv | work-dir/openeEuler-20.03-LTS-aarch64-dvd.iso.tests.json not exists,<br> work-dir/openeEuler-20.03-LTS-SP1-aarch64-dvd.iso.tests.json not exists,<br> work-dir/openeEuler-20.03-LTS-SP1-aarch64-dvd.iso.performance.json not exists,<br> work-dir/openeEuler-20.03-LTS-SP1-aarch64-dvd.iso.performance.json not exists |
| `RPMExtractDumper`                               | rpm提取的dumper，一次提取，多次使用                                       | repository,cache,config                                      | rpm解压提取的内容                                                                                      |                                                              |
| `ABIDumper`                                      | 依赖RPMExtractDumper接口，从rpm解压dumper中提取so库文件                    | repository,cahce,config                                      | so库文件字典封装                                                                                       |                                                              |
| `CmdDumper`                                      | 依赖RPMExtractDumper接口，从rpm解压dumper中提取cmd文件                    | repository,cahce,config                                      | cmd文件字典封装                                                                                       |                                                              |
| `ConfigDumper`                                   | 依赖RPMExtractDumper，从rpm解压dumper中提取配置文件                       | repository,cache,config                                      | 配置文件的字典封装                                                                                       |                                                              |
| `HeaderDumper`                                   | 依赖RPMExtractDumper，从rpm解压dumper中提取头文件                        | repository,cache,config                                      | 头文件的字典封装                                                                                        |                                                              |
| `JABIDumper`                                     | 依赖RPMExtractDumper，从rpm解压dumper中提取jar包                       | repository,cache,config                                      | jar包文件字典的封装                                                                                     |                                                              |
| `ServiceDumper`                                  | 依赖RPMExtractDumper，从rpm解压dumper中提取服务文件                       | repository,cache,config                                      | 服务文件字典的封装                                                                                       |                                                              |
| `KoDumper`                                       | 依赖RPMExtractDumper，从rpm解压dumper中提取ko文件                        | repository,cache,config                                      | 内核模块info信息及kabi列表封装成KoCompareExecutor可处理的对象                                                     |                                                              |
| `JABIDumper`                                     | 依赖RPMExtractDumper，从rpm解压dumper中提取jar包                       | repository,cache,config                                      | jar包文件字典的封装                                                                                     |                                                              |
| `FileListDumper`                                 | 获取rpm包内文件列表                                                  | repository,cache,config                                      | rpm包内文件列表的字典封装                                                                                  |                                                              |
| `PackageListDumper`                              | 获取仓库目录rpm包列表                                                 | directory,config                                             | 仓库目录所有rpm列表的字典封装                                                                                |                                                              |
| `ProvidesDumper`                                 | 获取rpm的provides                                               | repository,cache,config                                      | rpm的provides列表的字典封装                                                                             |                                                              |
| `RequiresDumper`                                 | 获取rpm的requires                                               | repository,cache,config                                      | rpm的requires列表的字典封装                                                                             |                                                              |
| `KabiDumper`                                     | 依赖RPMExtractDumper，解压kernel rpm后从symvers gz中提取kabi文件，经过白名单过滤 | repository,cache,config                                      | 内核接口内容的封装成NVSCompareExecutor可处理的对象                                                              |                                                              |
| `KconfigDumper`                                  | 依赖RPMExtractDumper，解压kernel rpm后从config文件中提取编译配置文件           | repository,cache,config                                      | 内核编译配置内容封装成NVSCompareExecutor可处理的对象                                                             |                                                              |
| `ABICompareExecutor`                             | 比较两个abi的dumper                                               | dump_a,dump_b,config                                         | abi比较结果对象树和差异保存到文件                                                                              |                                                              |
| `CmdCompareExecutor`                             | 比较两个命令文件的dumper                                              | dump_a,dump_b,config                                         | cmd比较结果对象树和差异保存到文件                                                                              |                                                              |
| `HeaderCompareExecutor`                          | 比较两个头文件的内容及头文件增加删除                                           | dump_a,dump_b,config                                         | 头文件比较结果对象树和差异保存到文件                                                                              |                                                              |
| `LibCompareExecutor`                             | 比较两个动态(.so)/静态库(.a)的dumper                                   | dump_a,dump_b,config                                         | lib的比较结果对象树和差异保存到文件                                                                             |                                                              |
| `ServiceCompareExecutor`                         | 比较两个服务文件的配置及服务文件增加删除                                         | dump_a,dump_b,config                                         | 服务文件的比较结果对象树和差异保存到文件                                                                            |
| `ListCompareExecutor`                            | 支持FileListDumper和PackageListDumper对象的dumper比较                | dump_a,dump_b,config                                         | 比较结果对象树                                                                                         |                                                              |
| `JABICompareExecutor`                            | 比较两个jabi的dumper                                              | dump_a,dump_b,config                                         | jabi的比较结果对象树和差异保存到文件                                                                            |                                                              |
| `KoCompareExecutor`                              | 比较两个内核模块的info信息及abi接口增加删除                               | dump_a,dump_b,config                                         | 比较结果对象树                                                                                         |                                                              |
| `NVSCompareExecutor`                             | 比较组件name/version/symbol的dumper                               | dump_a,dump_b,config                                         | 比较结果对象树                                                                                         |                                                              |
| `PlainCompareExecutor`                           | 比较config配置文件内容                                               | dump_a,dump_b,config                                         | 比较结果对象树和diff的文件内容                                                                               |                                                              |
| `CompareResultComposite.export`                  | 输出工具检测报告文件                                                   | 输出地址、输出格式、比较对象地址、平台测试文件地址                                        | 报告目录名                                                                                           |                                                              |




# 4、修改日志

| 版本 | 发布说明 |
| :--- | :------- |
|      |          |
|      |          |


# 5、参考目录

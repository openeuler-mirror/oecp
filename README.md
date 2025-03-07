
## 0. 说明

OECP工具聚焦openEuler内核和基础包，保障二次发行版生态核心特性不丢失，关键配置不更改 结合社区选包策略及软件包等级策略，检查L1、L2软件包版本、打包方式、接口一致性，KABI白名单，架构特性(如鲲鹏/X86特性)使能，性能优化配置，牵引实现扩展仓库openEuler系共享、共用，主流行业应用在openEuler系不同的OSV生态复用度90%。

1、检测2个ISO（基于RPM）的软件包，软件包内文件，库文件接口（C/C++）,内核KABI的变化差异

2、检测同一个软件（rpm包）在不同版本下的变化以及差异

3、**暂不支持嵌入式场景，敬请期待**

**检查项**

| 序号 | 检查                   |
| ---- | ---------------------- |
| 1    | 软件包检测             |
| 2    | 特性检测               |
| 3    | 配置检测               |

**验证项**

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


## 2. oecp下载安装与部署


install abidiff (centos): ''' yum install -y epel-release; yum install -y libabigail '''

install createrepo: ''' yum install -y createrepo '''

install binutils: ''' yum install -y binutils '''

注意：openeuler需要配置openEuler-20.03-SP2以上版本everything仓库
install abidiff (openEuler): ''' yum install -y libabigail '''

install oecp:
'''
git clone https://gitee.com/openeuler/oecp.git;
cd oecp;
pip3 install -r requirement
'''

## 3. oecp使用

`python3 cli.py [-h] [-n PARALLEL] [-w WORK_DIR] [-p PLAN_PATH]
                [-c CATEGORY_PATH] [--platform PLATFORM_TEST_PATH]
                [-f OUTPUT_FORMAT] [-o OUTPUT_FILE] [-d DEBUGINFO]
                file1 file2`
* **位置参数(必选)**
  * **`file`**
    指定两个比较的iso文件/存放rpm包的目录（directory）/rpm包，注意以file1作为基准

* **可选参数**

  * **`-n, --parallel`**
    指定`进程池并发数量`，默认cpu核数

  * **`-w, --work-dir`**
    指定`工作路径`，默认路径为/tmp/oecp
  
  * **`-p, --plan`**
    指定`比较计划`，默认为oecp/conf/plan/all.json

  * **`-c, --category`**
    指定`包级别信息`，默认为oecp/conf/category/category.json
	
  * **`-d, --debuginfo`**
    指定`debuginfo iso/rpm路径`
	
  * **`-f, --format`**
    指定`输出格式`，默认为csv

  * **`-b, --branch`**
    指定`kabi基线分支`，默认为20.03-LTS-SP1分支，可离线指定对比目标kabi白名单分支（比较对象为iso时工具可自行解析）

  * **`-a, --arch`**
    指定`架构`，指定比较架构，目前支持x86_64、aarch64（比较对象名内含架构时工具可自行解析）

  * **`-o, --output`**
    指定`输出结果路径`，默认为/tmp/oecp
  
  * **`-r, --rpm-name`**
    指定`输出软件包名称`，比较模式为内核配置文件、服务文件时，需指定文件所属软件包名称及-p比较计划根据文件类型配置'file'类型json配置文件

  * **`--platform`**
    指定`进行平台验证有关json报告地址`，默认为/tmp/oecp；性能测试默认基线文件为oecp/conf/performance/openEuler-20.03-LTS-aarch64-dvd.iso.performance.json
  
  * **`-s, --src_kernel`**
    指定`输入内核源码包路径`，路径下存放内核源码包：kernel-*.src.rpm，比较模式为kapi，需要在对应版本的kernel源码中查找kapi函数原型
  
* **举例**

  * **` python3 cli.py  /root/openEuler-20.03-LTS-aarch64-dvd.iso /root/openEuler-20.03-LTS-SP1-aarch64-dvd.iso`**

* **比较计划说明**
  * **`all.json`**
    涵盖下面所有配置项的比较
  * **`config.json`**
    比较rpm包中配置文件内容的差异，需依赖RPMExtractDumper（提取解压rpm的dumper类）
  * **`file_list.json`**
    比较rpm包文件列表差异，可通过rpm -pql ${rpm_path}命令获取rpm文件列表
  * **`kconfig.json`**
    比较内核配置文件，需依赖RPMExtractDumper（提取解压rpm的dumper类）
  * **`kabi.json`**
    比较内核kabi列表，需依赖RPMExtractDumper（提取解压rpm的dumper类）
  * **`kapi.json`**
    捕获kabi列表的kapi原型，比较内核kapi列表，需依赖RPMExtractDumper（提取解压rpm的dumper类）
  * **`package_list.json`**
    比较两个rpm包名称、版本、发行版本的差异
  * **`provides_requires.json`**
    比较rpm的provides和requires差异，可通过rpm -pq --provides/requires ${rpm_path}查询
  * **`abi.json`**
    比较rpm动态库文件的abi接口差异，使用abidiff工具（详细文档：https://sourceware.org/libabigail/manual/abidiff.html）
  * **`service.json`**
    比较rpm的默认服务配置，需依赖RPMExtractDumper（提取解压rpm的dumper类）
  * **`kabi_file.json`**
    比较内核kabi列表变化差异，输入比较目标为内核kabi列表文件（symvers*）时，指定比较计划-p为该json配置文件
  * **`kconfig_file.json`**
    比较内核配置变化差异，输入比较目标为内核配置文件（config-*）时，指定比较计划-p为该json配置文件
  * **`service_file.json`**
    比较服务文件配置变化差异，输入比较目标为服务文件（.service）时，指定比较计划-p为该json配置文件

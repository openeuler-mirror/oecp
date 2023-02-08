## 0. 主要功能

1.检测2个ISO（基于RPM）的软件包，软件包内文件，库文件接口（C/C++）,内核KABI的变化差异

2.检测同一个软件（rpm包）在不同版本下的变化以及差异
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

  * **`-o, --output`**
    指定`输出结果路径`，默认为/tmp/oecp

  * **`--platform`**
    指定`进行平台验证有关json报告地址`，默认为/tmp/oecp；性能测试默认基线文件为oecp/conf/performance/openEuler-20.03-LTS-aarch64-dvd.iso.performance.json
    
* **举例**

  * **` python3 cli.py  /root/openEuler-20.03-LTS-aarch64-dvd.iso /root/openEuler-20.03-LTS-SP1-aarch64-dvd.iso`**

* **比较计划说明**
  * **`all.json`**
    涵盖下面所有配置项的比较
  * **`config_file.json`**
    比较rpm包中配置文件内容的差异，需依赖RPMExtractDumper（提取解压rpm的dumper类）
  * **`file_list.json`**
    比较rpm包文件列表差异，可通过rpm -pql ${rpm_path}命令获取rpm文件列表
  * **`kconfig.json`**
    比较内核配置文件，需依赖RPMExtractDumper（提取解压rpm的dumper类）
  * **`package_list.json`**
    比较两个rpm包名称、版本、发行版本的差异
  * **`provides_requires.json`**
    比较rpm的provides和requires差异，可通过rpm -pq --provides/requires ${rpm_path}查询




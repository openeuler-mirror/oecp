# OECP报告展示后端详细设计文档

## 1 需求描述

​       搭建一个前端展示系统，通过上传OECP报告，对报告内容进行解析展示，提供 报告内容间的跳转链接，支持调用后端OECP工具能力，上传2个ISO，直接对比结果，无论何种方式得到的结果都保存下来，可用作后续查询。

### 1.1 依赖组件

|组件|组件描述|
|---|:-------|
| python3                        | python开发的软件，需要在python3的环境中运行         |
| flask | web框架，实现了wsgi协议 |
| flask-restful | flask框架的扩展，主要用于restfulapi接口开发 |
| sqlalchemy | 数据库交互的ORM映射框架，简化sql脚本编写 |
| pymysql | mysql数据库驱动链接 |
| marshmallow | API请求参数有效性校验、模型的序列化和反序列化 |
| celery | 异步任务处理（报告持久化、上传ISO、等待oecp工具分析） |
| xlrd==1.1 | 读取excel报告数据 |
| uwsgi | API服务部署的wsgi服务器 |
| redis | 配合celery异步任务使用，用于记录任务队列、状态 |

### 1.2 License

Mulan V2

## 2 设计概述

### 2.1 设计原则

- 数据与代码分离： 服务配置可动态调整，可变项应公开并可配置。

- 分层原则： 上层业务模块的数据查询应通过查询模块调用数据库获取数据，不可直接跨层访问数据库。

- 接口与实现分离：外部依赖模块接口而不是依赖模块实现。

- 模块划分： 模块之间只能单向调用，不能存在循环依赖。

- 变更： 架构设计变更、外部接口变更、特性需求变更需要结合开发、测试等所有相关人员经过开会讨论后决策，不可擅自变更。

## 3 需求分析

### 3.1.1 逻辑视图

![image-20220728223730627](imgs\逻辑视图.png)

### 3.1.2 ISO文件导入持久化

![image-20220728210530617](imgs\ISO文件导入流程)

> 1. ISO文件较大，采用分片上传技术，当所有分片上传成功后，调用分片合入（异步任务，后台进行分片合并）
> 2. 分片合并结束后，前端通过获取任务状态（合并已完成），向后台发送差异化分析请求，生成差异化分析与持久化异步任务
> 3. 调用OECP差异化分析工具，生成差异化报告，并通过持久化存储技术，对报告进行解析并存储

### 3.1.3 报告导入持久化

![image-20220728210451192](imgs\报告持久化流程)

> 1. 通过上传差异化报告，临时存放至系统指定目录中，调用异步任务（报告持久化存储），返回任务ID
> 2. 根据任务ID实时查看持久化进度，显示持久化结果

### 3.1.4 API开发视图

![image-20221017190153783](imgs\api开发视图)

### 3.1.5 部署视图

#### 	3.1.5.1 文件部署视图

![image-20220728235504886](imgs\文件部署视图)



#### 	3.1.5.2服务部署视图

![image-20220728210012176](imgs\服务部署视图)



### 3.2 属性设计

#### 3.2.1 软硬件配置

| 配置项   | 推荐规格                            |
| -------- | ----------------------------------- |
| CPU      | 8核                                 |
| 内存     | 32G                                 |
| 网络带宽 | 300M                                |
| I/O      | 375MB/sec                           |
| Mysql    | 版本8.2.0；单机部署可用，可部署集群 |

#### 3.2.2 性能规格

|规格名称|规格指标|
|:--|:-------|
|内存占用| 报告持久化过程中，内存占用不能超过1G |
|故障恢复| 系统故障恢复时间小于30min |
|响应时间| 上传后呈现结果5s内响应、点击链接跳转2s内响应 |
|ISO文件规格| 单个文件不能超过5G |
|日志规格| 日志限制大小转存储，单个日志文件不超过20M |
|报告上传并发数| 上传报告并发用户数10以上 |

#### 3.2.3 系统可靠性设计

1. **数据库**：

    备份恢复：系统增加定时任务，在特定的时间段内，对系统中的数据做备份，保留最新或最近的数据，便于后期恢复 ；

    主从复制：提升服务的稳定性，建议mysql数据库采用主从复制的部署方案，实现热切换；

2. **异常情况**：

  		后端API服务使用systemctl机制实现进程异常终止后，服务（uwsgi 部署的API）自启动；
  	
  		docker容器化部署，设置异常情况服务重启，可与docker compose/k8s配合使用;

3. **多请求并发场景处理**：

    报告上传/ISO分析时，采用任务队列方式，有序排队，减少内存占用或大量网络带宽；

    增加节流、限流机制，对相同的ip，分析接口使用的频次，定制化限制访问次数（60/min）;
    
4. **持久化保存**：
   
    用户上传的报告文件或oecp工具比对ISO生成的报告文件都将通过数据导入模块保存至mysql数据库，在持久化过程中，由于其他缘由导致服务不能正常完成的，应有状态机记录，在服务恢复后，予以重新导入。

#### 3.2.4 安全性设计

1. **数据库连接**：

    mysql数据库服务链接，用户名和密码均采用密文存放在环境变量中，通过获取环境变量值，链接数据库。

3. **多用户报告上传**：
    查询操作（读服务）所有用户均可操作，初始化操作（写服务）必须有软件管理员用户（安装时创建）或者root用户操作，代码中进行限制。

3. **文件权限**：

    采用权限最小化策略，主要文件权限如下：

    | 路径                                   | 属主      | 权限 | 描述            | 权限说明         |
    | -------------------------------------- | --------- | ---- | --------------- | ---------------- |
    | /lib/systemd/system/oecpreport.service | root root | 755  | service服务     | 启动/暂停api服务 |
    | /etc/oecp-report/conf.ini              | root root | 764  | api服务配置文件 | 读取/写入        |
    | /etc/oecp-report/oecp-report.ini       | root root | 764  | uwsgi启动配置   | 读取/写入        |
    | /var/log/oecp-report                   | root root | 764  | log日子存储路径 |                  |
    | /opt/oecp-report                       | root root | 750  | api程序         | 读取/执行        |

5. **服务启动：**

    **systemctl start oecpreport**只能由root用户启动

#### 3.2.5 兼容性设计

**支持多浏览器**：包括不限于Chrome、IE、Firefox 

**支持多分辨率**：包括不限于1920*1080、1024*768

### 3.3 特性清单

#### 3.3.1 原始需求

| 序号 | 描述                                                       |
| ---- | ---------------------------------------------------------- |
| 1    | 上传tar.gz压缩格式的报告，并展示报告的详细内容             |
| 2    | 展示报告所有信息                                           |
| 3    | 报告总览，支持点击报告总览单份报告标题，跳转到单份报告详情 |
| 4    | 点击单份报告详情里的数据，跳转到对应详细信息的功能         |
| 5    | 点击详细信息里的F列详情，可以跳转到单项更详细信息的功能    |
| 6    | 支持已有数据的查询                                         |
| 7    | 支持新增2个ISO数据对比生成报告和持久化                     |

#### 3.3.2 数据库设计

| 序号 | 数据表名                | 描述                    |
| ---- | ----------------------- | ----------------------- |
| 1    | abi_differences_compare | abi变化对比             |
| 2    | report_change_info      | 报告变化信息表          |
| 3    | report_base             | 报告主表                |
| 4    | rpmfile_analyse         | rpm文件分析             |
| 5    | all_rpm_report          | 对比分析所有rpm包的结果 |
| 6    | report_detail_base      | 报告详情主表            |
| 7    | osv_technical_report    | OSV技术评测报告         |
| 8    | interface_change        | 接口变化                |
| 9    | kernel                  | kernel内核              |
| 10   | md_detail               | 过程中md文件            |
| 11   | diff_service_detail     | 服务变化详情            |
| 12   | rpm_requires_analyse    | rpm依赖分析             |

![image-20221017201718639](imgs\数据库结构设计)

#### 3.3.3 数据表字段解释

> **abi_differences_compare**
>
> **abi变化对比**

| 字段           | 备注              | 类型         | Null  | 默认值 |
| -------------- | ----------------- | ------------ | ----- | ------ |
| id             | abi变化对比表主键 | int          | False | NA     |
| report_base_id | 报告主表id        | int          | False | NA     |
| rpm_package    | rpm包名           | varchar(200) | true  |        |
| source         | abi变化的源       | varchar(200) | true  |        |
| compare        | abi变化对比的包   | varchar(200) | true  |        |
| compare_result | 对比的结果        | varchar(50)  | true  |        |
| compare_type   | 对比类型          | varchar(20)  | true  |        |
| category_level | 比对级别          | varchar(20)  | true  |        |
| effect_drivers | 官方驱动          | varchar(500) | true  |        |
| detail_path    | 详细路径          | varchar(500) | true  |        |

> **report_change_info**
>
> **报告变化信息表**

| 字段           | 备注                 | 类型        | Null  | 默认值 |
| -------------- | -------------------- | ----------- | ----- | ------ |
| id             | 报告变化信息表主键   | int         | False | NA     |
| report_base_id | 报告主表id           | int         | False | NA     |
| r_delete       | 删除                 | varchar(20) | true  |        |
| r_add          | 新增                 | varchar(20) | true  |        |
| r_release      | release              | varchar(20) | true  |        |
| version_update | 版本升级             | varchar(20) | true  |        |
| consistent     | 保持一致             | varchar(20) | true  |        |
| provide_change | provide变化          | varchar(20) | true  |        |
| require_change | require变化          | varchar(20) | true  |        |
| level          | 级别（全量、L1、L2） | varchar(10) | true  | ALL    |

> **report_base**
>
> **报告主表**

| 字段           | 备注          | 类型         | Null  | 默认值 |
| -------------- | ------------- | ------------ | ----- | ------ |
| id             | 报告主键      | int          | False | NA     |
| title          | 报告标题      | int          | False |        |
| source_version | 源-比对版本   | varchar(200) | false |        |
| target_version | 目标-比对版本 | varchar(200) | false |        |
| state          | 状态          | varchar(200) | false |        |
| create_time    | 创建时间      | datetime     | false |        |

> **rpmfile_analyse**
>
> **rpm文件分析**

| 字段                | 备注            | 类型        | Null  | 默认值 |
| ------------------- | --------------- | ----------- | ----- | ------ |
| id                  | rpm文件分析主键 | int         | False | NA     |
| report_base_id      | 报告主表id      | int         | False | NA     |
| rpm_type            | rpm类型         | varchar(5)  | False |        |
| rpm_level           | rpm的等级       | varchar(10) | False |        |
| package_chanage     | 软件包变化      | varchar(50) | False |        |
| file_more           | 文件增加        | varchar(50) | False |        |
| file_less           | 文件减少        | varchar(50) | False |        |
| file_consistent     | 文件一致        | varchar(50) | False |        |
| file_content_change | 文件内容变化    | varchar(50) | False |        |

> **all_rpm_report**
>
> **对比分析所有rpm包的结果**

| 字段                       | 备注           | 类型         | Null  | 默认值 |
| -------------------------- | -------------- | ------------ | ----- | ------ |
| id                         | 报告主键       | int          | False | NA     |
| report_base_id             | 报告主表id     | int          | False | NA     |
| source_binary_rpm_package  | 源头的二进制包 | varchar(200) | false |        |
| source_src_package         | 源头的源码包   | varchar(200) | false |        |
| compare_binary_rpm_package | 比对的二进制包 | varchar(200) | false |        |
| compare_src_package        | 比对的源码包   | varchar(200) | false |        |
| compare_result             | 对比的结果     | varchar(500) | true  |        |
| compare_type               | 对比类型       | varchar(50)  | true  |        |
| category_level             | 划分等级       | varchar(50)  | true  |        |
| more                       | 更多           | varchar(20)  | true  |        |
| less                       | 减少           | varchar(20)  | true  |        |
| diff                       | 不同           | varchar(20)  | true  |        |
| same                       |                | varchar(20)  | true  |        |

> **report_detail_base**
>
> **报告详情主表**

| 字段           | 备注             | 类型         | Null  | 默认值 |
| -------------- | ---------------- | ------------ | ----- | ------ |
| id             | 报告主键         | int          | False | NA     |
| report_base_id | 报告主表id       | int          | False | NA     |
| rpm_package    | rpm包名          | varchar(200) | false |        |
| source         | 源头包           | varchar(200) | false |        |
| compare        | 比对包           | varchar(200) | false |        |
| compare_result | 对比的结果       | varchar(50)  | true  |        |
| compare_type   | 对比类型         | varchar(20)  | true  |        |
| category_level | 划分等级         | varchar(20)  | true  |        |
| effect_drivers | 官方驱动         | varchar(500) | true  |        |
| md_detail_path | md文件路径       | varchar(500) | true  |        |
| detail_path    | 对比结果文件路径 | varchar(200) | true  |        |

> **osv_technical_report**
>
> **OSV技术评测报告**

| 字段              | 备注                | 类型         | Null  | 默认值 |
| ----------------- | ------------------- | ------------ | ----- | ------ |
| id                | 报告主键            | int          | False | NA     |
| report_base_id    | 报告主表id          | int          | False | NA     |
| osv_version       | osv版本             | varchar(50)  | false |        |
| architecture      | 架构                | varchar(20)  | false |        |
| release_addr      | 发布地址            | varchar(200) | false |        |
| checksum          | checksum            | varchar(20)  | true  |        |
| base_home_old_ver | 基于home/old/的版本 | varchar(200) | true  |        |
| detection_result  | 检测结果            | varchar(20)  | true  |        |
| detail_json       | 检测详情json        | text         | true  |        |

> **interface_change**
>
> **接口变化**

| 字段             | 备注         | 类型        | Null  | 默认值 |
| ---------------- | ------------ | ----------- | ----- | ------ |
| id               | 报告主键     | int         | False | NA     |
| report_base_id   | 报告主表id   | int         | False | NA     |
| interface_change | 接口变化     | varchar(20) | true  |        |
| interface_add    | 接口增加     | varchar(20) | true  |        |
| interface_del    | 接口删除     | varchar(20) | true  |        |
| param_change     | 参数数量变化 | varchar(20) | true  |        |
| struct_change    | 结构体变化   | varchar(20) | true  |        |
| struct_del       | 结构体删除   | varchar(20) | true  |        |
| struct_add       | 增加结构体   | varchar(20) | true  |        |
| level            | 级别         | varchar(10) | true  |        |

> **kernel**
>
> **kernel内核**

| 字段           | 备注               | 类型        | Null  | 默认值 |
| -------------- | ------------------ | ----------- | ----- | ------ |
| id             | kernel内核表主键id | int         | False | NA     |
| report_base_id | 报告主表id         | int         | False | NA     |
| kernel_analyse | kernel内核分析     | varchar(50) | true  |        |
| more           | 增加               | int         | true  | 0      |
| less           | 减少               | int         | true  | 0      |
| same           | 不变               | int         | true  | 0      |
| diff           | 发生变化           | int         | true  | 0      |

> **md_detail**
>
> **过程中md文件**

| 字段           | 备注             | 类型         | Null  | 默认值 |
| -------------- | ---------------- | ------------ | ----- | ------ |
| id             | 过程中MD文件表id | int          | False | NA     |
| report_base_id | 报告主表id       | int          | False | NA     |
| detail_path    | 详情路径         | varchar(500) | False |        |
| md_content     | md文档内容       | text         | False |        |

> **diff_service_detail**
>
> **服务变化详情**

| 字段           | 备注                 | 类型         | Null  | 默认值 |
| -------------- | -------------------- | ------------ | ----- | ------ |
| id             | 服务变化详情表主键id | int          | False | NA     |
| report_base_id | 报告主表id           | int          | False | NA     |
| rpm_package    | rpm包名              | varchar(200) |       |        |
| source         | 服务变化对比的源     | varchar(200) |       |        |
| compare        | 服务变化需要对比的包 | varchar(200) |       |        |
| compare_result | 比对的结果           | varchar(50)  |       |        |
| compare_type   | 比对的类型           | varchar(20)  |       |        |
| file_name      | 文件名称             | varchar(500) |       |        |
| detail_path    | 详情路径             | varchar(500) |       |        |

> **rpm_requires_analyse**
>
> **rpm依赖分析**

| 字段                    | 备注              | 类型         | Null  | 默认值 |
| ----------------------- | ----------------- | ------------ | ----- | ------ |
| id                      | rpm依赖分析主键id | int          | False | NA     |
| report_base_id          | 报告主表id        | int          | False | NA     |
| rpm_package             | rpm包名           | varchar(200) |       |        |
| source_symbol_name      |                   | text         |       |        |
| source_package          | 源包名称          | text         |       |        |
| source_dependence_type  | 源依赖的类型      | varchar(20)  |       |        |
| compare_symbol_name     |                   | text         |       |        |
| compare_package         | 比对的包          | text         |       |        |
| compare_dependence_type | 比对的起来类型    | varchar(20)  |       |        |
| compare_result          | 比对的结果        | varchar(50)  |       |        |
| compare_type            | 比对的类型        | varchar(20)  |       |        |
| category_level          | 分析的类型        | varchar(20)  |       |        |
| detail_path             | 详细路径          | varchar(500) |       |        |

### 3.4 API接口清单

| 序号 | 接口名称 | 类型 | 说明 |
|    - |   - |    - |   - |
| 1 | /upload/tar-gz | post | 上传tar.gz压缩格式的报告，读取报告内容存入数据库 |
| 2 | /upload/ios | post | 上传两个IOS文件，生成对比报告，并将报告内容存入数据库 |
| 3    | /upload/exists/upload-file                                   | get  | 判断上传的文件是否存在                                    |
| 4    | /upload/async/state/<str:task_id>                            | get  | 获取后台任务状态                                          |
| 5    | /upload/analysis/iso                                         | post | 通过oecp工具分析iso底层变化,生成报告                      |
| 6    | /upload/storage/iso                                          | get  | ISO镜像文件获取或删除                                     |
| 7    | /report/detail/all-rpm/page/<int:limit>/<int:page>           | get  | 分页查询所有rpm对比报告详细信息                           |
| 8    | /report/page/<int:limit>/<int:page>                          | get  | 分页查询报告总览信息                                      |
| 9    | /report/detail/osv/<int:report_base_id>                      | get  | 查询OSV技术测评报告                                       |
| 10   | /report/detail/all-differences/page/<int:limit>/<int:page>   | get  | 分页查询所有比对出的差异文件                              |
| 11   | /report/detail/all-compare/page/<int:limit>/<int:page>       | get  | 分页查询比对报告详情                                      |
| 12   | /report/compare/iso-info/<int:report_base_id>                | get  | 获取比较的iso名称                                         |
| 13 | /report/compare/all-compare-type/<int:report_base_id> | get | 获取所有比较类型 |
| 14 | /report/compare/all-compare-result/<int:report_base_id> | get | 对比ISo的差异，主要用于获取比较的基本信息（ISO1 VS ISO2） |
| 15 | /report/update-version/<int:report_base_id> | post | 修改报告标题/删除报告 |
| 16 | /report/md-detail/<int:report_base_id> | get | md文档详情 |
| 17   | /report/diff-service-csv-detail/page/<int:limit>/<int:page>  | get  | diff service报告详情列表                                  |
| 18 | /statistical/detail/all-package/<int:report_base_id> | get | 查询软件包比对统计 |
| 19 | /statistical/detail/rpm-service-cmd-conf/<int:report_base_id> | get | 查询rpm 的服务文件、命令、配置文件比对结果 |
| 20 | /statistical/detail/api-change/<int:report_base_id> | get | 查询接口文件变化、接口参数变化、结构体变化统计 |
| 21 | /statistical/detail/kernel-analyse/<int:report_base_id>      | get  | kernel内核分析统计数据查询                                |
| 22   | /statistical/detail/rpmfile-analyse/<int:report_base_id>     | get  | rpm文件分析统计                                           |

>**备注：后续所有API请求都包含msg、code、data三个标准字段，视情况而定，data可以是字典也可能是数组，具体请参照API**
>
>```json
># 示例：
>{
>    "code": "200",
>    "data": []/{},
>    "msg": ""
>}
>```

#### 3.4.1  /upload/tar-gz

- 描述: 上传tar.gz压缩格式的报告，读取报告内容存入数据库

- HTTP请求方式：POST

- 数据提交方式：application/form

- 请求参数：

  | 参数名 | 必选 | 类型 | 说明                         |
  | ------ | ---- | ---- | ---------------------------- |
  | file   | True | File | 要上传的tar.gz压缩格式的报告 |

- 返回体参数

  | 参数名 | 类型 | 说明 |
  |    - |   - |    - |
  | code | str | 状态码 |
  | msg | str | 状态码对应的信息 |
  
- 返回体参数示例

```json
{
    "code": "200",
    "msg": ""
}
```

#### 3.4.2  /upload/ios

- 描述: 上传两个IOS文件，生成对比报告，并将报告内容存入数据库

- HTTP请求方式：POST

- 数据提交方式：application/form

- 请求参数：

  | 参数名      | 必选 | 类型 | 说明                          |
  | ----------- | ---- | ---- | ----------------------------- |
  | file_source | True | File | 要生成比对报告的第一个ISO文件 |
  | file_targ   | True | File | 要生成比对报告的第二个ISO文件 |

- 返回体参数

  | 参数名 | 类型 | 说明             |
  | ------ | ---- | ---------------- |
  | code   | str  | 状态码           |
  | msg    | str  | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "msg": ""
}
```

#### 3.4.3 /upload/exists/upload-file

- 描述: 判断上传的文件是否存在

- HTTP请求方式：GET

- 数据提交方式：application/json

  | 参数名   | 必选 | 类型 | 说明      |
  | -------- | ---- | ---- | --------- |
  | filename | True | str  | ISO文件名 |

- 返回体参数

  | 参数名 | 类型 | 说明                        |
  | ------ | ---- | --------------------------- |
  | code   | str  | 状态码                      |
  | data   | bool | 存在（true）不存在（false） |
  | msg    | str  | 状态码对应的信息            |

- 返回体参数示例

```json
{
    "code": "200",
    "data": true/false,
    "msg": ""
}
```

#### 3.4.4 /upload/async/state/<str:task_id>

- 描述: 获取异步任务的状态

- HTTP请求方式：GET

- 数据提交方式：application/json

  | 参数名  | 必选 | 类型 | 说明       |
  | ------- | ---- | ---- | ---------- |
  | task_id | True | str  | 异步任务id |

- 返回体参数

  | 参数名 | 类型 | 说明                     |
  | ------ | ---- | ------------------------ |
  | code   | str  | 状态码                   |
  | data   | json | 异步任务的执行结果和状态 |
  | msg    | str  | 状态码对应的信息         |

- 返回体参数示例

```json
{
    "code": "200",
    "data": {
        "result":"异步任务执行结果",
        "status":"异步任务当前状态"
    },
    "msg": ""
}
```

#### 3.4.5 /upload/analysis/iso

- 描述: 通过oecp工具分析iso底层变化,生成报告

- HTTP请求方式：POST

- 数据提交方式：application/json

  | 参数名     | 必选 | 类型 | 说明        |
  | ---------- | ---- | ---- | ----------- |
  | source_iso | True | str  | 源iso文件   |
  | target_iso | True | str  | 目标iso文件 |

- 返回体参数

  | 参数名 | 类型 | 说明             |
  | ------ | ---- | ---------------- |
  | code   | str  | 状态码           |
  | data   | str  | 异步任务id       |
  | msg    | str  | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": "分析iso变化的任务id",
    "msg": ""
}
```

#### 3.4.6 /upload/storage/iso

- 描述: 获取存储的iso文件或删除iso文件

- HTTP请求方式：GET/DELETE

- 数据提交方式：application/json

  | 参数名   | 必选  | 类型 | 说明                                                |
  | -------- | ----- | ---- | --------------------------------------------------- |
  | filename | False | str  | 需要删除的iso文件名称，当请求为delete方式时，必传项 |

- 返回体参数

  | 参数名 | 类型  | 说明             |
  | ------ | ----- | ---------------- |
  | code   | str   | 状态码           |
  | data   | array | 存储的文件名列表 |
  | msg    | str   | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": ["file1","file2"], // 只有get请求时才为array列表
    "msg": ""
}
```

#### 3.4.7  /report/detail/all-rpm/page/<int:limit>/<int:page>

- 描述: 分页查询对比报告详细信息

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选  | 类型 | 说明                   |
  | -------------- | ----- | ---- | ---------------------- |
  | page           | True  | int  | 分页查询参数：页码     |
  | limit          | True  | int  | 分页查询参数：每页条数 |
  | report_base_id | True  | int  | 比对报告主表id         |
  | compare_type   | False | str  | 对比文件类型           |
  | compare_result | False | str  | 对比结果               |
  | category_level | False | int  | 分类等级               |
  | key_word       | false | str  | 查询关键字             |
  | order_by       | false | str  | 排序字段               |
  | order_by_mode  | false | str  | 排序模式（asc, desc）  |

- 返回体参数

  | 参数名 | 类型 | 说明             |
  | ------ | ---- | ---------------- |
  | code   | str  | 状态码           |
  | data   | json | 分页查询结果数据 |
  | msg    | str  | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": {
        "total": 0,
        "pages": [{
            "id":1,
            "source_binary_rpm_package":"Cunit-1.1.rpm",
            "source_src_package":"Cunit-1.1.src.rpm",
            "compare_binary_rpm_package":"Cunit-2.1.rpm",
            "compare_src_package":"Cunit-2.1.src.rpm",
            "compare_result":"",
            "compare_detail":"",
            "compare_type":"rpm file",
            "category_level":1,
            "more":2,
            "less":3,
            "diff":5,
            "report_base_id":1,
        }]
    },
    "msg": ""
}
```

#### 3.4.8  /report/page/<int:limit>/<int:page>

- 描述: 分页查询报告总览信息

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名        | 必选  | 类型 | 说明                   |
  | ------------- | ----- | ---- | ---------------------- |
  | page          | True  | int  | 分页查询参数：查询页码 |
  | limit         | True  | int  | 分页查询参数：每页条数 |
  | order_by      | false | str  | 排序字段               |
  | order_by_mode | false | str  | 排序模式（asc, desc）  |
  | level         | True  | str  | 等级（ALL 、L1、 L2）  |

- 返回体参数

  | 参数名 | 类型 | 说明             |
  | ------ | ---- | ---------------- |
  | code   | str  | 状态码           |
  | data   | json | 返回查询结果     |
  | msg    | str  | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": {
        "total": 0,
        "pages": [{
            "id":1,
            "report_base_id":1,
            "r_delete":"200",
            "r_add":"120",
            "r_release":"35",
            "version_update":"218",
            "consistent":"996",
            "provide_change":"128",
            "require_change":"256",
            "version":"Centos6vsCentos7"
        }]
    },
    "msg": ""
}
```

#### 3.4.9  /report/detail/osv/<int:report_base_id>

- 描述: 查询OSV技术测评报告

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选 | 类型 | 说明           |
  | -------------- | ---- | ---- | -------------- |
  | report_base_id | True | int  | 比对报告主表id |

- 返回体参数

  | 参数名 | 类型 | 说明             |
  | ------ | ---- | ---------------- |
  | code   | str  | 状态码           |
  | data   | json | OSV技术测评报告  |
  | msg    | str  | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": {
        "osv_version":"1.2.3",
        "architecture":"arch64",
        "release_addr":"/home/oecp",
        "checksum":3,
        "base_home_old_ver":"1.2.0",
        "detection_result":"通过",
        "detail_json":"",
    },
    "msg": ""
}
```

#### 3.4.10  /report/detail/all-differences/page/<int:limit>/<int:page>

- 描述: 分页查询所有比对出的差异文件

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选  | 类型 | 说明                   |
  | -------------- | ----- | ---- | ---------------------- |
  | page           | True  | int  | 分页查询参数：页码     |
  | limit          | True  | int  | 分页查询参数：每页条数 |
  | report_base_id | True  | int  | 比对报告主表id         |
  | compare_type   | False | str  | 对比文件类型           |
  | compare_result | False | str  | 对比结果               |
  | category_level | False | int  | 分类等级               |
  | key_word       | false | str  | 查询关键字             |
  | order_by       | false | str  | 排序字段               |
  | order_by_mode  | false | str  | 排序模式（asc, desc）  |

- 返回体参数

  | 参数名 | 类型 | 说明             |
  | ------ | ---- | ---------------- |
  | code   | str  | 状态码           |
  | data   | json | 分页查询结果数据 |
  | msg    | str  | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": {},
    "msg": ""
}
```

#### 3.4.11    /report/detail/all-compare/page/<int:limit>/<int:page>

- 描述: 分页查询比对报告详情

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选  | 类型 | 说明                   |
  | -------------- | ----- | ---- | ---------------------- |
  | page           | True  | int  | 分页查询参数：页码     |
  | limit          | True  | int  | 分页查询参数：每页条数 |
  | report_base_id | True  | int  | 比对报告主表id         |
  | compare_type   | False | str  | 对比文件类型           |
  | compare_result | False | str  | 对比结果               |
  | category_level | False | int  | 分类等级               |
  | key_word       | false | str  | 查询关键字             |
  | order_by       | false | str  | 排序字段               |
  | order_by_mode  | false | str  | 排序模式（asc, desc）  |

- 返回体参数

  | 参数名 | 类型 | 说明             |
  | ------ | ---- | ---------------- |
  | code   | str  | 状态码           |
  | data   | json | 分页查询结果数据 |
  | msg    | str  | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": {
        "total": 0,
        "pages": [
            {
                "id":1,
                "rpm_package":"23",
                "source":"Cunit-1.1",
                "compare":"Cunit-2.1",
                "compare_result":"123",
                "compare_type":"123",
                "category_level":"2",
                "abi_detail":"",
            }
        ]
    },
    "msg": ""
}
```

#### 3.4.12   /report/compare/iso-info/<int:report_base_id>

- 描述: 对比ISo的差异，主要用于获取比较的基本信息（ISO1 VS ISO2）

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选 | 类型 | 说明           |
  | -------------- | ---- | ---- | -------------- |
  | report_base_id | True | int  | 比对报告主表id |

- 返回体参数

  | 参数名 | 类型 | 说明              |
  | ------ | ---- | ----------------- |
  | code   | str  | 状态码            |
  | data   | json | 比较的iso基本信息 |
  | msg    | str  | 状态码对应的信息  |

- 返回体参数示例

```json
{
    "code": "200",
    "data": {
        "source":"比对的源ISO",
        "target":"比对的目标ISO"
    },
    "msg": ""
}
```

#### 3.4.13   /report/compare/all-compare-type/<int:report_base_id>

- 描述: 获取所有比较类型

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名 | 必选 | 类型 | 说明                                                         |
  | ------ | ---- | ---- | ------------------------------------------------------------ |
  | key    | True | str  | 比对的类型（detail、compare、different、diffservice）数值是其中之一 |

- 返回体参数

  | 参数名 | 类型  | 说明             |
  | ------ | ----- | ---------------- |
  | code   | str   | 状态码           |
  | data   | array | 比对的类型       |
  | msg    | str   | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": [{
        "compare_type": "比对的类型"
    }],
    "msg": ""
}
```

#### 3.4.14  /report/compare/all-compare-result/<int:report_base_id>

- 描述: 获取所有比对结果

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名 | 必选 | 类型 | 说明                                                         |
  | ------ | ---- | ---- | ------------------------------------------------------------ |
  | key    | True | str  | 比对的类型（detail、compare、different、diffservice）数值是其中之一 |

- 返回体参数

  | 参数名 | 类型  | 说明             |
  | ------ | ----- | ---------------- |
  | code   | str   | 状态码           |
  | data   | array | 比对的类型       |
  | msg    | str   | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": [{
        "compare_result": "比对的结果"
    }],
    "msg": ""
}
```

#### 3.4.15  /report/update-version/<int:report_base_id>

- 描述: 修改报告标题/删除报告

- HTTP请求方式：POST/DELETE

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选  | 类型 | 说明                                         |
  | -------------- | ----- | ---- | -------------------------------------------- |
  | version        | False | str  | 待更新的标题，**当请求方式为POST时，必传项** |
  | report_base_id | True  | int  | 报告的id                                     |

- 返回体参数

  | 参数名 | 类型 | 说明             |
  | ------ | ---- | ---------------- |
  | code   | str  | 状态码           |
  | data   | str  | 成功与否的提示语 |
  | msg    | str  | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": "",
    "msg": ""
}
```

#### 3.4.16  /report/md-detail/<int:report_base_id>

- 描述: md文档详情

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选 | 类型 | 说明     |
  | -------------- | ---- | ---- | -------- |
  | report_base_id | True | int  | 报告的id |

- 返回体参数

  | 参数名 | 类型 | 说明             |
  | ------ | ---- | ---------------- |
  | code   | str  | 状态码           |
  | data   | json | md文档的内容     |
  | msg    | str  | 状态码对应的信息 |

- 返回体参数示例

```json
{
    "code": "200",
    "data": {
        "id": "md主键id",
        "detail_path": "详情路径",
        "md_content": "md的内容"
    },
    "msg": ""
}
```

#### 3.4.17  /report/diff-service-csv-detail/page/<int:limit>/<int:page>

- 描述: service文件变化详情

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选  | 类型 | 说明                                |
  | -------------- | ----- | ---- | ----------------------------------- |
  | report_base_id | True  | int  | 报告的id                            |
  | path           | True  | str  | 文档详情地址                        |
  | order_by       | False | str  | 排序字段                            |
  | order_by_mode  | False | str  | 排序的模式 升序（asc） 降序 （dsc） |
  | compare_type   | False | str  | 比对的类型                          |
  | compare_result | False | str  | 比对的结果                          |

- 返回体参数

  | 参数名 | 类型 | 说明                      |
  | ------ | ---- | ------------------------- |
  | code   | str  | 状态码                    |
  | data   | json | service文件变化的结果列表 |
  | msg    | str  | 状态码对应的信息          |

- 返回体参数示例

```json
{
    "code": "200",
    "data": {
        "total": 0,
        "pages":[
            {
               "id": "service diff 主键id",
                "report_base_id": "报告id",
                "rpm_package": "rpm包名",
                "source": "源比对的包",
                "compare": "待比对的包",
                "compare_result": "比对的结果",
                "compare_type": "比对的类型",
                "file_name": "文件名"
            }
        ]
    },
    "msg": ""
}
```

#### 3.4.18   /statistical/detail/all-package/<int:report_base_id>

- 描述: 查询软件包比对统计

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选 | 类型 | 说明           |
  | -------------- | ---- | ---- | -------------- |
  | report_base_id | True | int  | 比对报告主表id |

- 返回体参数

  | 参数名 | 类型  | 说明                   |
  | ------ | ----- | ---------------------- |
  | code   | str   | 状态码                 |
  | data   | array | 软件包比对结果统计列表 |
  | msg    | str   | 状态码对应的信息       |

- 返回体参数示例

```json
{
    "code": "200",
    "data": [
        {
            "r_delete":"1",
            "r_add":"23",
            "r_release":'345',
            "version_update":"1232",
            "consistent":"123",
            "provide_change":"234",
            "require_change":"3",
            "level":"ALL/L1/L2"
        }
    ],
    "msg": ""
}
```

#### 3.4.19  /statistical/detail/rpm-service-cmd-conf/<int:report_base_id>

- 描述: 查询rpm 的服务文件、命令、配置文件比对结果

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选 | 类型 | 说明           |
  | -------------- | ---- | ---- | -------------- |
  | report_base_id | True | int  | 比对报告主表id |

- 返回体参数

  | 参数名 | 类型  | 说明                   |
  | ------ | ----- | ---------------------- |
  | code   | str   | 状态码                 |
  | data   | array | 软件包比对结果统计列表 |
  | msg    | str   | 状态码对应的信息       |

- 返回体参数示例

```json
{
    "code": "200",
    "data": [
        {
            "service_rpm_change":"123",
            "service_file_add":"213",
            "service_file_less":"23",
            "service_file":"123",
            "service_file_name":"34",
            "service_file_path":"232",
            "cmd_rpm_change":"988",
            "cmd_file_add":"12",
            "cmd_file_less":"123",
            "cmd_file":"23",
            "cmd_file_name":"123",
            "cmd_file_path":"567",
            "conf_rpm_change":"56",
            "conf_file_add":"2",
            "conf_file_less":"45",
            "conf_file":"89",
            "conf_file_name":"998",
            "conf_file_path":"23",
            "level":"ALL/L1/L2",
        }
    ],
    "msg": ""
}
```

#### 3.4.20  /statistical/detail/change-api/<int:report_base_id>

- 描述: 查询接口文件变化、接口参数变化、结构体变化统计

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选 | 类型 | 说明           |
  | -------------- | ---- | ---- | -------------- |
  | report_base_id | True | int  | 比对报告主表id |

- 返回体参数

  | 参数名 | 类型  | 说明                 |
  | ------ | ----- | -------------------- |
  | code   | str   | 状态码               |
  | data   | array | 接口比对结果统计列表 |
  | msg    | str   | 状态码对应的信息     |

- 返回体参数示例

```json
{
    "code": "200",
    "data": [
        {
            "interface_change":"12",
            "interface_add":"3432",
            "interface_del":"23",
            "param_change":"567",
            "struct_change":"232",
            "struct_del":"567",
            "struct_add":"12",
            "level":"ALL/L1/L2",
        }
    ],
    "msg": ""
}
```

#### 3.4.21  /statistical/detail/kernel-analyse/<int:report_base_id>

- 描述: kernel内核分析统计数据查询

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选 | 类型 | 说明           |
  | -------------- | ---- | ---- | -------------- |
  | report_base_id | True | int  | 比对报告主表id |

- 返回体参数

  | 参数名 | 类型  | 说明               |
  | ------ | ----- | ------------------ |
  | code   | str   | 状态码             |
  | data   | array | kernel分析统计数组 |
  | msg    | str   | 状态码对应的信息   |

- 返回体参数示例

```json
{
    "code": "200",
    "data": [{
        "kernel_analyse": "kernel分析项",
        "more": "增加",
        "less": "减少",
        "same": "一致",
        "diff": "变化"
    }],
    "msg": ""
}
```

#### 3.4.22  /statistical/detail/rpmfile-analyse/<int:report_base_id>

- 描述: rpm文件分析统计

- HTTP请求方式：GET

- 数据提交方式：application/json

- 请求参数：

  | 参数名         | 必选 | 类型 | 说明           |
  | -------------- | ---- | ---- | -------------- |
  | report_base_id | True | int  | 比对报告主表id |

- 返回体参数

  | 参数名 | 类型  | 说明                |
  | ------ | ----- | ------------------- |
  | code   | str   | 状态码              |
  | data   | array | rpm文件分析统计数组 |
  | msg    | str   | 状态码对应的信息    |

- 返回体参数示例

```json
{
    "code": "200",
    "data": [{
        "rpm_type": "rpm类型",
        "rpm_level": "rpm等级",
        "package_change": "变化的包",
        "file_more": "增加的文件",
        "file_less": "减少的文件",
        "file_consistent": "一致的文件",
        "file_content_change": "内容变化的文件"
    }],
    "msg": ""
}
```

### 3.5 配置文件选项

```ini
[DATABASE]
; mysql数据库用户名
db_account=root
; mysql数据库连接密码
db_password=
; 数据库主机地址
db_host=
; 连接数据库的端口号
db_port=3306
; 数据库名称
database=
; redis缓存数据库连接地址
redis=127.0.0.1:6379

[LOG]
; 日志保存的路径
log_path=/var/log/oecp
; log日志名称
log_name=oecp-report.log
; 日志的等级
log_level=INFO
; 日志最大保存个数
log_backup_count=2
; 日志输出格式
log_formatter= %(asctime)s===%(filename)s——>[line:%(lineno)d]-%(levelname)s-【Detail Info】: %(message)s
; 单个日志文件最大字节数
log_max_bytes=102400

[SOURCES]
; 临时文件、上传保存的文件地址
workspace=/tmp/oecp-report
; oecp分析工具入口文件
cli=/app/oecp/cli.py

; API启动时wsgi服务配置项
[UWSGI]
http=:5000
module=manage:app
chdir=/app
callable=app
pidfile=oecp-report.pid
enable-threads=true
touch-logreopen=.touch_for_logrotate
daemonize=/var/log/oecp/oecp-api.log
```

### 3.6 内部模块接口清单

| 模块                     | 接口名称               | 描述                                                         |
| ------------------------ | ---------------------- | ------------------------------------------------------------ |
| libs.sql                 | DataBase               | sqlalchemy orm操作封装，简化链接、添加、删除等               |
| libs.url                 | include                | 加入flask蓝图和restful API服务                               |
| libs.url                 | module_string          | 传入模块路径，自动解析导包                                   |
| libs.conf                | configs                | 融合系统默认配置项和用户配置项（用户配置项优先级**高于**系统默认配置） |
| libs.command             | cmd                    | 对suprocess.popen的封装，简化命令行调用                      |
| libs.response            | respmsg.body           | 统一的response响应消息                                       |
| application.apps.base    | dberror                | 捕获数据库操作异常装饰器，统一处理数据库服务错误响应         |
| application.apps.base    | validate               | API请求数据有效性校验装饰器                                  |
| application.apps.base    | ApiView                | view的封装，针对响应成功、失败、定制化响应的操作             |
| application.core.storage | AnalysisReport.storage | 分析差异化报告，构建分析数据，持久化存储                     |
| application.core.storage | tar_gz                 | 解压gzip压缩包                                               |
| application.core.storage | unpack_tar             | 解压tar压缩包                                                |

#### 3.6.1 orm sql模块

##### Database

- 类/接口描述：

​		sqlalchemy orm操作封装，简化链接、添加、删除等

- 初始化参数

| 参数名    | 必填 | 类型 | 说明           |
| --------- | ---- | ---- | -------------- |
| user_name | 否   | str  | 数据库用户名   |
| password  | 否   | str  | 数据库链接密码 |
| host      | 否   | str  | 链接主机地址   |
| port      | 否   | int  | 数据库端口号   |
| db_name   | 否   | str  | 数据库名称     |

- 请求示例

```python
with Database(user_name,password,host,port,db_name) as db:
    pass
```

#### 3.6.2 url路由模块

##### include

- 方法描述

​		加入flask蓝图和restful API服务

- 调用参数

| 参数名     | 必填 | 类型 | 说明                         |
| ---------- | ---- | ---- | ---------------------------- |
| module     | 是   | str  | 路由模块，传递模块的完整路径 |
| api_prefix | 是   | str  | api路由前缀                  |

- 请求示例

```python
include(("application.apps.api_model", "api/v1"))
```

- 返回示例

```python
return blue_print,api
```

##### module_string

- 方法描述

​		传入模块路径，自动解析导包

- 调用参数

| 参数名        | 必填 | 类型 | 说明               |
| ------------- | ---- | ---- | ------------------ |
| module_path   | 是   | str  | 模块的完整路径     |
| import_module | 否   | bool | 导入模块，存在类名 |

- 返回示例

```python
return getattr(module, class_name)
```

#### 3.6.3 配置模块

##### Configs

- 类/接口描述

​		融合系统默认配置项和用户配置项（用户配置项优先级**高于**系统默认配置）

- 调用参数

| 参数名    | 必填 | 类型 | 说明             |
| --------- | ---- | ---- | ---------------- |
| conf_file | 是   | str  | 用户配置文件路径 |

- 请求示例

```python
Configs(settings_file)
```

#### 3.6.4 命令行执行模块

##### cmd

- 类/接口描述

​		针对suprocess.popen的封装，简化命令行调用

- 调用参数

| 参数名 | 必填 | 类型 | 说明                               |
| ------ | ---- | ---- | ---------------------------------- |
| cmds   | 是   | str  | 命令语句                           |
| cwd    | 否   | str  | 在特定的目录下执行命令（目录地址） |

- 请求示例

```python
cmd(cmds="dnf install -y xx")
```

- 返回示例

```python
return code,out,error
```

| 参数名 | 类型 | 说明                                   |
| ------ | ---- | -------------------------------------- |
| code   | int  | 命令行执行的结果，0表示成功，非0则失败 |
| out    | str  | 命令执行过程中的输出                   |
| error  | str  | 执行失败后，打印错误信息               |

#### 3.6.5 response响应信息

##### respmsg.body

- 类/接口描述

​		统一的response响应消息

- 调用参数

| 参数名  | 必填 | 类型   | 说明                                               |
| ------- | ---- | ------ | -------------------------------------------------- |
| label   | 是   | str    | 定义的响应状态标签，根据标签换取提示信息           |
| zh      | 否   | bool   | 为True时则获取中文提示信息，反之则获取英文提示信息 |
| tip     | 否   | bool   | 前端自动提示信息时是否需要展示弹框                 |
| data    | 否   | object | 具体响应的数据结果                                 |
| message | 否   | str    | 定制化的响应消息                                   |

-  请求示例

```python
respmsg.body(label=response.FAIL, message=message,data=object)
```

- 返回示例

```json
{
    "message":"成功",
    "code":200,
    "data":{},
    "tip":false
}
```

| 参数名  | 类型   | 说明                                        |
| ------- | ------ | ------------------------------------------- |
| message | str    | 展示的消息内容                              |
| code    | int    | 响应的状态码，常见有200、400、500           |
| data    | object | 响应的具体数据，可能是object、array两种形式 |
| tip     | bool   | 前端自动处理框架是否需要展示提示信息        |

#### 3.6.6 API公共视图

##### dberror

- 类/接口描述

​		捕获数据库操作异常装饰器，统一处理数据库服务错误响应

- 调用参数

​		暂无，只需要作为装饰器使用

- 请求示例

```python
@dberror
def fun():
    pass
```

##### validate

- 类/接口描述

​		API请求数据有效性校验装饰器

- 调用参数

​		暂无，只需作为装饰器使用

- 请求示例

```python
@validate
def fun():
    pass
```

##### ApiView

- 类/接口描述

​		view的封装，针对响应成功、失败、定制化响应的操作

- 调用参数

​		暂无，继承自Resource，api实现过程中的类皆需继承ApiView

- 请求示例

```python
class LoginApi(ApiView):
    pass
```

#### 3.6.7 报告解析存储

##### AnalysisReport.storage

- 接口/类描述

​		分析差异化报告，构建分析数据，持久化存储

- 调用参数

| 参数名 | 必填 | 类型 | 说明                                    |
| ------ | ---- | ---- | --------------------------------------- |
| title  | 是   | str  | 导入报告的标题                          |
| file   | 否   | str  | tar报告压缩包，只有是报告上传时需要传递 |
| clean  | 否   | bool | 对上一次的临时目录做清理                |
| iso    | 否   | bool | iso对比生成的报告                       |

- 请求示例

```python
analysis_report = AnalysisReport()
analysis_report.storage(title=title, clean=False, iso=True)
```

- 异常信息

​		**DatabaseException**：数据库导入时发生错误

​		**FileNotFoundError**：指定的文件不存在

​		**ValueError**：提供的报告格式不正确

​		**IOError**：解压缩时文件压缩格式不正确

##### tar_gz

- 接口/类描述

​		解压gzip压缩包

- 调用参数

| 参数名      | 必填 | 类型 | 说明               |
| ----------- | ---- | ---- | ------------------ |
| gz_file     | 是   | str  | 待解压的压缩包     |
| unpack_file | 是   | str  | 解压后的文件新名称 |

- 请求示例

```python
tar_gz(gz_file="/tmp/xxx.tar.gz", unpack_file="/tmp/xxx.tar")
```

##### unpack_tar

-  接口/类描述

​		解压tar压缩包

- 调用参数

| 参数名        | 必填 | 类型 | 说明                  |
| ------------- | ---- | ---- | --------------------- |
| tar_file      | 是   | str  | tar包的完整名称       |
| unpack_folder | 是   | str  | tar包解压后存放的路径 |

- 请求示例

```python
unpack_tar(tar_file="/tmp/xxx.tar", unpack_folder="/tmp/tar-folder")
```




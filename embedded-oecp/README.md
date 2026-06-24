<!--
Copyright (c) Huawei Technologies Co., Ltd. 2026-2026. All rights reserved.
[embedded-oecp] is licensed under the Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
    http://license.coscl.org.cn/MulanPSL2
THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
PURPOSE.
See the Mulan PSL v2 for more details.
-->

# embedded-oecp

openEuler Embedded OSV 兼容性认证自动化测试工具

## 概述

`embedded-oecp` 是 [oecp](https://atomgit.com/openeuler/oecp)（openEuler 兼容性检测工具）的嵌入式子系统，专门为 **openEuler Embedded 嵌入式系统**打造。

工具将 OSV 兼容性认证标准转化为可自动化执行的检测项，覆盖**源码认证、构建认证、运行时认证**三大类共 9 项检测，自动在构建环境和目标设备上执行测试，收集证据截图，并基于 docx 模板生成标准认证测试报告。

## 快速开始

### 前置条件

```bash
pip install -r requirements.txt
```

### 使用流程

```bash
# 1. 进入 embedded-oecp 目录
cd oecp/embedded-oecp

# 2. 编辑配置（构建目录、设备 IP、架构等）
vim workdir/conf/config.yaml

# 3. 执行测试并生成报告
python3 cli.py run -p all
python3 cli.py report
```

## 运行方式

工具通过 `python3 cli.py` 运行（与服务器版 oecp 一致）。工作目录固定为 `embedded-oecp/workdir/`，首次运行时自动创建目录结构并复制默认配置，无需手动初始化。

### 工作目录结构

```
embedded-oecp/
├── cli.py                        # 入口脚本
└── workdir/                      # 工作目录（自动创建）
    ├── conf/
    │   ├── config.yaml           # 配置文件（.gitignore，不上传）
    │   └── config.yaml.sample    # 配置模板（参考用）
    ├── cache/                    # 测试结果缓存（JSON）
    └── report/
        ├── evidence/             # 证据文件（截图、日志、Excel）
        ├── summary.json          # JSON 格式完整结果
        ├── summary.txt           # 终端友好摘要
        └── openEuler_Embedded_OSV_认证测试报告_*.docx
```

```bash
# 所有命令在 embedded-oecp 目录下运行
python3 cli.py run -p all
python3 cli.py summary
python3 cli.py report
python3 cli.py list
python3 cli.py cache list
```

## 认证检查项

### 源码认证（3 项）

| 子项 | 检查器 | 说明 |
|------|--------|------|
| 内核 | `KernelChecker` | 5 步检查：manifest 信息 → 仓库在 openEuler 组织 → 本地与 manifest 一致 → 版本在主流范围(5.10/6.6) → 目标设备内核版本 |
| 基础中间件 | `MiddlewareChecker` | 3 步 MD5 比对：目标设备提取 libc.so MD5 → env.yaml 获取基线 → 比对结果 |
| 其他软件包 | `PackageChecker` | 镜像依赖包来源检查，生成 Excel 列表并嵌入报告，社区包占比 ≥ 70% |

### 构建认证（3 项）

| 子项 | 检查器 | 说明 |
|------|--------|------|
| 编译链 | `CompilerChecker` | 3 步 MD5 检查：env.yaml 获取 gcc/glibc 基线 → 构建环境提取 MD5 → 比对 |
| 构建工程 | `ProjectChecker` | 2 步检查：oebuild bitbake 命令可用 → 构建目录结构合规（cache/conf/output/tmp 等） |
| 包列表 | `PkgListChecker` | 社区包版本一致性检查（基于 manifest.yaml 基线 + pkgdata 映射 + 辅助配方排除），一致率 ≥ 70% |

### 运行时认证（3 项）

| 子项 | 检查器 | 说明 |
|------|--------|------|
| C库运行时 | `MiddlewareRuntimeChecker` | 2 步：上传 glib-abi-check 检测程序并校验 MD5 → 在目标设备运行 ABI 检测 |
| 基础功能(AT) | `ATTestChecker` | 通过 mugen 执行社区 AT 测试用例，解析 combination_results，保存完整执行日志 |
| POSIX | `PosixChecker` | 通过 mugen 执行 POSIX 测试用例（embedded_osv_posix.json），保存完整执行日志 |

## 包列表检查（PkgListChecker）详细逻辑

包列表检查对镜像 manifest 中的每个软件包进行社区包版本一致性验证，采用三层过滤机制：

### 三层过滤流程

```
镜像 manifest（如 2242 包）
  │
  ├─ ① 排除 packagegroup 包（如 packagegroup-core-boot）
  │
  ├─ ② 判断是否社区包：在 manifest.yaml 基线中查找
  │    ├─ 在基线中 → 社区包 → 从 openeuler/ 源码目录获取 remote，与基线比对版本一致性
  │    └─ 不在基线 → 非社区包
  │
  └─ ③ 排除辅助配方（无实体源码的 Yocto 配方）
       条件：PV == "1.0" 且 SRC_URI 为空或仅含 file:// 本地文件（无压缩包）
       判定方式：oebuild bitbake -e <pn> 获取 SRC_URI
       示例：systemd-compat-units（SRC_URI=""）、keymaps（file://keymap.sh）
```

### 关键技术点

- **PKG 反向映射**：Yocto 会将包名重命名（如 `libnl` → `libnl-3-200`），通过 pkgdata 中的 `PKG:` 字段建立反向映射，确保重命名后的包也能找到源码信息
- **pkgdata 直接读取**：从 `tmp/pkgdata/{MACHINE}/runtime/` 文件直接读取 `OPENEULER_LOCAL_NAME`、`PN`、`PV`，不调用 oebuild 命令（避免超时）
- **辅助配方识别**：通过 `oebuild bitbake -e <recipe>` 获取 SRC_URI，结合 PV=1.0 判断是否为无实体源码的辅助配方（配置脚本类），排除出统计范围
- **基线获取**：从 `baseline_repo`（`baseline_branch`）指定的仓库远程获取 `.oebuild/manifest.yaml`，作为社区包判断和版本比对的权威基线
- **一致性分母**：排除 packagegroup 包和辅助配方后的所有包（含非社区包），非社区包和社区包无源码目录均计入分母

### 一致率计算

```
一致率 = 社区包版本一致数 / (总包数 - packagegroup包数 - 辅助配方数)
```

## 使用方法

> 以下所有命令均在 `embedded-oecp/` 目录下通过 `python3 cli.py` 执行。

### 1. 运行全部检测

```bash
python3 cli.py run -p all
```

### 2. 运行指定类别的检测

```bash
# 仅源码认证
python3 cli.py run -p source

# 仅构建认证
python3 cli.py run -p build

# 仅运行时认证
python3 cli.py run -p runtime
```

### 3. 运行指定检测项

```bash
# 单独运行内核检查
python3 cli.py run -p kernel

# 单独运行包列表检查
python3 cli.py run -p pkglist

# 强制忽略缓存重新执行
python3 cli.py run -p at_test --no-cache
```

### 4. 查看结果

```bash
# 查看汇总（基于缓存）
python3 cli.py summary

# 列出所有测试项
python3 cli.py list
```

### 5. 生成报告

```bash
# 基于缓存结果生成 docx 认证报告
python3 cli.py report
```

### 6. 保存配置

```bash
# 将命令行参数写入 workdir/conf/config.yaml
python3 cli.py -d /path/to/build --arch aarch64 --device-ip 192.168.1.100 save

# 保存到指定文件
python3 cli.py -d /path/to/build --arch aarch64 save -o /path/to/config.yaml
```

### 7. 缓存管理

```bash
# 列出缓存状态
python3 cli.py cache list

# 清理全部缓存
python3 cli.py cache clear

# 清理指定检测项缓存
python3 cli.py cache clear -p posix
```

### 8. 命令行参数覆盖

命令行参数会覆盖配置文件中的值，无需修改配置文件即可临时调整：

```bash
# 临时指定构建目录和设备
python3 cli.py -d /path/to/build --device-ip 192.168.1.100 run -p all
```

## 命令行参数

### 全局参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-c, --config` | 配置文件路径（覆盖 workdir/conf/config.yaml） | - |
| `-d, --image-build-dir` | 镜像编译目录（构建工程根目录） | - |
| `--arch` | 目标架构: aarch64/arm32/x86_64/riscv64 | - |
| `--toolchain-dir` | 编译工具链目录 | - |
| `--device-ip` | 目标设备 IP 地址 | - |
| `--device-user` | 目标设备 SSH 用户名 | `root` |
| `--device-password` | 目标设备 SSH 密码 | - |
| `--build-timestamp` | 镜像编译时间戳 | - |
| `--sdk-file` | 镜像 SDK 文件路径（自动计算 MD5） | - |
| `-v, --verbose` | 详细输出 | - |

### 子命令

| 子命令 | 说明 |
|--------|------|
| `run [-p PLAN] [--no-cache]` | 执行测试 |
| `summary` | 测试结果汇总 |
| `report` | 生成认证报告 |
| `list` | 列出所有测试项 |
| `cache <list\|clear> [-p PLAN]` | 缓存管理 |
| `save [-o FILE]` | 保存配置 |

### run 子命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-p, --plan` | 测试计划: all / source / build / runtime / 具体测试项名 | `all` |
| `--no-cache` | 忽略缓存，强制重新执行 | - |

## 输出报告

工具生成以下文件（位于 `workdir/report/` 下）：

1. **DOCX 报告** — 基于 docx 模板生成的完整认证测试报告，含封面页、基本信息、测试环境、各检测项结果（含截图证据）、汇总表和认证结论
2. **summary.json** — 机器可读的 JSON 格式完整结果
3. **summary.txt** — 终端友好的摘要报告
4. **evidence/** — 证据目录（终端截图 PNG + AT/POSIX 执行日志 + Excel 依赖包列表）

### 报告特性

- 封面页（系统名称、公司名称、拟制/审核行，宋体 42pt）
- 截图证据使用终端风格渲染（Catppuccin 深色主题，中文字体支持）
- AT 和 POSIX 测试附加完整执行日志文件（Ole10Native 格式嵌入 docx）
- 包列表检查结果以 Excel 附件形式嵌入 docx（OLE 附件，可双击打开）
- 自动 SSH 连接目标设备获取 `/etc/os-release` 信息
- 认证结论根据汇总结果自动生成（全部 PASS → 通过，有 FAIL → 不通过，有 NONE → 待整改）
- 全文档统一宋体字体，表格内五号字（10.5pt）

## 缓存机制

每次测试结果以 JSON 文件缓存在 `workdir/cache/` 下。`run` 命令默认先查缓存，有则直接使用；`summary` 和 `report` 命令基于缓存生成。使用 `--no-cache` 可强制重新执行。

## 配置文件

配置文件位于 `workdir/conf/config.yaml`，首次运行时自动从包内默认配置复制。可参考 `workdir/conf/config.yaml.sample` 了解配置项。`work_dir` 和 `output_dir` 不需要配置，由工作目录自动决定。`source_dir` 自动从 `image_build.dir/../../src` 推导。

主要配置项：

```yaml
# 基线仓库（社区包版本基线）
baseline_repo: https://atomgit.com/openeuler/yocto-meta-openeuler.git
baseline_branch: master

# 构建相关
image_build:
  dir: /path/to/build/dir          # 镜像构建目录
arch: aarch64
toolchain:
  dir: /path/to/toolchain          # 编译工具链目录

# 目标设备
device:
  ip: 192.168.1.100
  user: root
  password: xxx
  port: 22

# mugen 测试框架
mugen:
  at_config: embedded_osv_at.json
  posix_config: embedded_osv_posix.json
  remote: https://atomgit.com/openeuler/mugen.git
  branch: master
  sdk_install_dir: /opt/sdk
```

### 自动推导的路径

| 配置项 | 推导规则 | 示例 |
|--------|----------|------|
| `work_dir` | `embedded-oecp/workdir` | `/home/ubuntu/demo/oecp/embedded-oecp/workdir` |
| `output_dir` | `workdir/report` | `.../workdir/report` |
| `cache` | `workdir/cache` | `.../workdir/cache` |
| `source_dir` | `image_build.dir/../../src` | `/home/ubuntu/demo/src` |

## 项目结构

```
embedded-oecp/
├── cli.py                          # 入口脚本（python3 cli.py）
├── embedded_oecp/                  # 核心代码包
│   ├── cli.py                      # CLI 逻辑（参数解析、子命令分发）
│   ├── default_config.yaml         # 包内默认配置（首次自动复制到 workdir/conf/）
│   ├── models.py                   # 数据模型（TestResult, TestStatus, TEST_ITEMS）
│   ├── runner.py                   # 测试运行器（CHECKER_MAP, resolve_checkers, 缓存查询）
│   ├── checkers/                   # 检查器
│   │   ├── __init__.py             # BaseChecker 基类（get_build_dir/get_source_dir）
│   │   ├── source/                 # 源码认证
│   │   │   ├── kernel_checker.py
│   │   │   ├── middleware_checker.py
│   │   │   └── package_checker.py
│   │   ├── build/                  # 构建认证
│   │   │   ├── compiler_checker.py
│   │   │   ├── project_checker.py
│   │   │   └── pkglist_checker.py
│   │   └── runtime/                # 运行时认证
│   │       ├── middleware_runtime_checker.py
│   │       ├── at_test_checker.py
│   │       └── posix_checker.py
│   ├── report/
│   │   └── generator.py            # 报告生成器（docx 模板 + OLE 嵌入）
│   ├── cache/
│   │   └── __init__.py             # 结果缓存（JSON 文件）
│   ├── assets/                     # 资源文件（随包打包）
│   │   ├── report_template.docx    # 报告模板
│   │   ├── embedded_osv_at.json    # AT 测试 mugen 配置模板
│   │   ├── embedded_osv_posix.json # POSIX 测试 mugen 配置模板
│   │   ├── excel_icon.png          # Excel OLE 嵌入图标
│   │   ├── log_icon.png            # 日志 OLE 嵌入图标
│   └── utils/
│       ├── config.py               # 配置加载 + workdir 管理
│       ├── logger.py               # 日志
│       ├── shell.py                # 本地命令执行 + paramiko SSH 远程执行
│       ├── terminal_screenshot.py  # 终端风格截图（Catppuccin 深色主题）
│       ├── screenshot.py           # 浏览器截图
│       ├── env_yaml.py             # env.yaml 解析与远端获取
│       ├── git.py                  # git 操作
│       └── md5.py                  # MD5 计算
├── workdir/                        # 工作目录（自动创建）
│   ├── conf/
│   │   ├── config.yaml             # 用户配置（.gitignore）
│   │   └── config.yaml.sample      # 配置模板
│   ├── cache/                      # 测试结果缓存
│   └── report/evidence/            # 报告与证据文件
├── tests/
│   └── test_basic.py               # 单元测试
├── requirements.txt
├── setup.cfg / setup.py / pyproject.toml
└── README.md
```

## License

MulanPSL-2.0

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

openEuler Embedded OSV Compatibility Certification Automation Tool

## Overview

`embedded-oecp` is the embedded subsystem of [oecp](https://atomgit.com/openeuler/oecp) (openEuler Compatibility Detection Tool), designed specifically for **openEuler Embedded** systems.

The tool translates OSV compatibility certification standards into automated detection items, covering **source certification, build certification, and runtime certification** — 9 items in total. It executes tests on the build environment and target devices, collects evidence screenshots, and generates standard certification reports based on a docx template.

## Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

### Workflow

```bash
# 1. Enter the embedded-oecp directory
cd oecp/embedded-oecp

# 2. Edit configuration (build directory, device IP, architecture, etc.)
vim workdir/conf/config.yaml

# 3. Run tests and generate report
python3 cli.py run -p all
python3 cli.py report
```

## Execution Model

The tool runs via `python3 cli.py` (consistent with the server-side oecp). The working directory is fixed at `embedded-oecp/workdir/`. The directory structure and default configuration are created automatically on first run — no manual initialization required.

### Working Directory Structure

```
embedded-oecp/
├── cli.py                        # Entry script
└── workdir/                      # Working directory (auto-created)
    ├── conf/
    │   ├── config.yaml           # Configuration file (.gitignore'd)
    │   └── config.yaml.sample    # Configuration template
    ├── cache/                    # Test result cache (JSON)
    └── report/
        ├── evidence/             # Evidence files (screenshots, logs, Excel)
        ├── summary.json          # Machine-readable JSON results
        ├── summary.txt           # Terminal-friendly summary
        └── openEuler_Embedded_OSV_Certification_Report_*.docx
```

```bash
# All commands run from the embedded-oecp directory
python3 cli.py run -p all
python3 cli.py summary
python3 cli.py report
python3 cli.py list
python3 cli.py cache list
```

## Certification Items

### Source Certification (3 items)

| Sub-item | Checker | Description |
|----------|---------|-------------|
| Kernel | `KernelChecker` | 5-step check: manifest info → repo in openEuler org → local matches manifest → version in mainstream range (5.10/6.6) → target device kernel version |
| Middleware | `MiddlewareChecker` | 3-step MD5 comparison: extract libc.so MD5 from target → get baseline from env.yaml → compare |
| Other Packages | `PackageChecker` | Image dependency package source check, generates Excel list embedded in report, community package ratio ≥ 70% |

### Build Certification (3 items)

| Sub-item | Checker | Description |
|----------|---------|-------------|
| Compiler Chain | `CompilerChecker` | 3-step MD5 check: get gcc/glibc baseline from env.yaml → extract MD5 from build env → compare |
| Build Project | `ProjectChecker` | 2-step check: oebuild bitbake command available → build directory structure compliant (cache/conf/output/tmp, etc.) |
| Package List | `PkgListChecker` | Community package version consistency check (based on manifest.yaml baseline + pkgdata mapping + auxiliary recipe exclusion), consistency rate ≥ 70% |

### Runtime Certification (3 items)

| Sub-item | Checker | Description |
|----------|---------|-------------|
| C Library Runtime | `MiddlewareRuntimeChecker` | 2-step: upload glib-abi-check tool and verify MD5 → run ABI check on target device |
| Basic Functions (AT) | `ATTestChecker` | Execute community AT test cases via mugen, parse combination_results, save full execution logs |
| POSIX | `PosixChecker` | Execute POSIX test cases via mugen (embedded_osv_posix.json), save full execution logs |

## Package List Check (PkgListChecker) Details

The package list check verifies version consistency for each package in the image manifest against the community baseline, using a three-layer filtering mechanism:

### Three-Layer Filtering

```
Image manifest (e.g., 2242 packages)
  │
  ├─ ① Exclude packagegroup packages (e.g., packagegroup-core-boot)
  │
  ├─ ② Determine if community package: lookup in manifest.yaml baseline
  │    ├─ In baseline → community package → get remote from openeuler/ source dir, compare version
  │    └─ Not in baseline → non-community package
  │
  └─ ③ Exclude auxiliary recipes (recipes without real source code)
       Condition: PV == "1.0" AND SRC_URI is empty or only file:// entries (no archives)
       Method: oebuild bitbake -e <pn> to get SRC_URI
       Examples: systemd-compat-units (SRC_URI=""), keymaps (file://keymap.sh)
```

### Key Technical Points

- **PKG reverse mapping**: Yocto renames packages (e.g., `libnl` → `libnl-3-200`). The `PKG:` field in pkgdata is used to build a reverse mapping so renamed packages can be resolved to their source info
- **Direct pkgdata reading**: Reads `OPENEULER_LOCAL_NAME`, `PN`, `PV` directly from `tmp/pkgdata/{MACHINE}/runtime/` files without calling oebuild commands (avoids timeout)
- **Auxiliary recipe identification**: Uses `oebuild bitbake -e <recipe>` to get SRC_URI, combined with PV=1.0 to determine if a recipe has no real source code (config/script type), excluded from statistics
- **Baseline fetching**: Fetches `.oebuild/manifest.yaml` from the repository specified by `baseline_repo` (`baseline_branch`) as the authoritative baseline for community package determination and version comparison
- **Consistency denominator**: All packages after excluding packagegroup and auxiliary recipes (including non-community packages). Non-community packages and community packages without source directories are counted in the denominator

### Consistency Rate Calculation

```
Consistency rate = matched community packages / (total packages - packagegroup count - auxiliary recipe count)
```

## Usage

> All commands are executed from the `embedded-oecp/` directory via `python3 cli.py`.

### 1. Run All Checks

```bash
python3 cli.py run -p all
```

### 2. Run by Category

```bash
# Source certification only
python3 cli.py run -p source

# Build certification only
python3 cli.py run -p build

# Runtime certification only
python3 cli.py run -p runtime
```

### 3. Run Specific Check

```bash
# Kernel check only
python3 cli.py run -p kernel

# Package list check only
python3 cli.py run -p pkglist

# Force re-run ignoring cache
python3 cli.py run -p at_test --no-cache
```

### 4. View Results

```bash
# Summary (from cache)
python3 cli.py summary

# List all test items
python3 cli.py list
```

### 5. Generate Report

```bash
# Generate docx certification report from cached results
python3 cli.py report
```

### 6. Save Configuration

```bash
# Save CLI arguments to workdir/conf/config.yaml
python3 cli.py -d /path/to/build --arch aarch64 --device-ip 192.168.1.100 save

# Save to specific file
python3 cli.py -d /path/to/build --arch aarch64 save -o /path/to/config.yaml
```

### 7. Cache Management

```bash
# List cache status
python3 cli.py cache list

# Clear all cache
python3 cli.py cache clear

# Clear specific check cache
python3 cli.py cache clear -p posix
```

### 8. CLI Argument Override

CLI arguments override configuration file values — no need to modify the config file for temporary adjustments:

```bash
# Temporarily specify build directory and device
python3 cli.py -d /path/to/build --device-ip 192.168.1.100 run -p all
```

## CLI Arguments

### Global Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `-c, --config` | Configuration file path (overrides workdir/conf/config.yaml) | - |
| `-d, --image-build-dir` | Image build directory (build project root) | - |
| `--arch` | Target architecture: aarch64/arm32/x86_64/riscv64 | - |
| `--toolchain-dir` | Compiler toolchain directory | - |
| `--device-ip` | Target device IP address | - |
| `--device-user` | Target device SSH username | `root` |
| `--device-password` | Target device SSH password | - |
| `--build-timestamp` | Image build timestamp | - |
| `--sdk-file` | Image SDK file path (auto-compute MD5) | - |
| `-v, --verbose` | Verbose output | - |

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `run [-p PLAN] [--no-cache]` | Execute tests |
| `summary` | Test result summary |
| `report` | Generate certification report |
| `list` | List all test items |
| `cache <list\|clear> [-p PLAN]` | Cache management |
| `save [-o FILE]` | Save configuration |

### run subcommand

| Argument | Description | Default |
|----------|-------------|---------|
| `-p, --plan` | Test plan: all / source / build / runtime / specific check name | `all` |
| `--no-cache` | Ignore cache, force re-run | - |

## Output Report

The tool generates the following files (under `workdir/report/`):

1. **DOCX Report** — Full certification test report based on docx template, including cover page, basic info, test environment, each check result (with screenshot evidence), summary table, and certification conclusion
2. **summary.json** — Machine-readable JSON format full results
3. **summary.txt** — Terminal-friendly summary report
4. **evidence/** — Evidence directory (terminal screenshots PNG + AT/POSIX execution logs + Excel dependency list)

### Report Features

- Cover page (system name, company name, prepared/reviewed by, SimSun 42pt)
- Screenshot evidence rendered in terminal style (Catppuccin dark theme, CJK font support)
- AT and POSIX tests attach full execution log files (Ole10Native format embedded in docx)
- Package list check results embedded as Excel attachment in docx (OLE attachment, double-click to open)
- Automatically SSH to target device to retrieve `/etc/os-release` info
- Certification conclusion auto-generated based on summary (all PASS → certified, any FAIL → not certified, any NONE → pending remediation)
- Unified SimSun font throughout, 10.5pt in tables

## Cache Mechanism

Each test result is cached as a JSON file under `workdir/cache/`. The `run` command checks cache first by default; `summary` and `report` commands generate output from cache. Use `--no-cache` to force re-execution.

## Configuration

The configuration file is located at `workdir/conf/config.yaml`, auto-copied from the package default on first run. Refer to `workdir/conf/config.yaml.sample` for available options. `work_dir` and `output_dir` are determined automatically by the working directory. `source_dir` is derived from `image_build.dir/../../src`.

Main configuration items:

```yaml
# Baseline repository (community package version baseline)
baseline_repo: https://atomgit.com/openeuler/yocto-meta-openeuler.git
baseline_branch: master

# Build
image_build:
  dir: /path/to/build/dir          # Image build directory
arch: aarch64
toolchain:
  dir: /path/to/toolchain          # Compiler toolchain directory

# Target device
device:
  ip: 192.168.1.100
  user: root
  password: xxx
  port: 22

# mugen test framework
mugen:
  at_config: embedded_osv_at.json
  posix_config: embedded_osv_posix.json
  remote: https://atomgit.com/openeuler/mugen.git
  branch: master
  sdk_install_dir: /opt/sdk
```

### Auto-derived Paths

| Config | Derivation Rule | Example |
|--------|-----------------|---------|
| `work_dir` | `embedded-oecp/workdir` | `/home/ubuntu/demo/oecp/embedded-oecp/workdir` |
| `output_dir` | `workdir/report` | `.../workdir/report` |
| `cache` | `workdir/cache` | `.../workdir/cache` |
| `source_dir` | `image_build.dir/../../src` | `/home/ubuntu/demo/src` |

## Project Structure

```
embedded-oecp/
├── cli.py                          # Entry script (python3 cli.py)
├── embedded_oecp/                  # Core package
│   ├── cli.py                      # CLI logic (argument parsing, subcommand dispatch)
│   ├── default_config.yaml         # Default config (auto-copied to workdir/conf/ on first run)
│   ├── models.py                   # Data models (TestResult, TestStatus, TEST_ITEMS)
│   ├── runner.py                   # Test runner (CHECKER_MAP, resolve_checkers, cache lookup)
│   ├── checkers/                   # Checkers
│   │   ├── __init__.py             # BaseChecker base class (get_build_dir/get_source_dir)
│   │   ├── source/                 # Source certification
│   │   │   ├── kernel_checker.py
│   │   │   ├── middleware_checker.py
│   │   │   └── package_checker.py
│   │   ├── build/                  # Build certification
│   │   │   ├── compiler_checker.py
│   │   │   ├── project_checker.py
│   │   │   └── pkglist_checker.py
│   │   └── runtime/                # Runtime certification
│   │       ├── middleware_runtime_checker.py
│   │       ├── at_test_checker.py
│   │       └── posix_checker.py
│   ├── report/
│   │   └── generator.py            # Report generator (docx template + OLE embedding)
│   ├── cache/
│   │   └── __init__.py             # Result cache (JSON files)
│   ├── assets/                     # Resource files (packaged)
│   │   ├── report_template.docx    # Report template
│   │   ├── embedded_osv_at.json    # AT test mugen config template
│   │   ├── embedded_osv_posix.json # POSIX test mugen config template
│   │   ├── excel_icon.png          # Excel OLE embed icon
│   │   ├── log_icon.png            # Log OLE embed icon
│   └── utils/
│       ├── config.py               # Config loading + workdir management
│       ├── logger.py               # Logging
│       ├── shell.py                # Local command execution + paramiko SSH
│       ├── terminal_screenshot.py  # Terminal-style screenshot (Catppuccin dark theme)
│       ├── screenshot.py           # Browser screenshot
│       ├── env_yaml.py             # env.yaml parsing and remote fetching
│       ├── git.py                  # Git operations
│       └── md5.py                  # MD5 computation
├── workdir/                        # Working directory (auto-created)
│   ├── conf/
│   │   ├── config.yaml             # User config (.gitignore'd)
│   │   └── config.yaml.sample      # Config template
│   ├── cache/                      # Test result cache
│   └── report/evidence/            # Reports and evidence files
├── tests/
│   └── test_basic.py               # Unit tests
├── requirements.txt
├── setup.cfg / setup.py / pyproject.toml
└── README.md
```

## License

MulanPSL-2.0

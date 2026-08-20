English | [简体中文](./README.md)

# oecp

## 0. Description

The OECP tool focuses on the openEuler kernel and base packages, ensuring that core features of secondary distributions are preserved and key configurations remain unchanged. Combined with the community package selection policy and the package level strategy, it checks L1/L2 package versions, packaging methods, interface consistency, the KABI whitelist, enablement of architecture features (e.g., Kunpeng/X86 features), and performance optimization configurations. It drives the sharing and reuse of extended repositories across the openEuler ecosystem, aiming for a 90% reuse rate of mainstream industry applications across different OSVs in the openEuler ecosystem.

1. Detect differences between two ISOs (RPM-based): packages, files inside packages, library file interfaces (C/C++), and kernel KABI changes
2. Detect changes and differences of the same software (rpm package) across different versions
3. **Embedded scenarios are not supported yet. Stay tuned.**

**Check items**

| No. | Check |
| --- | --- |
| 1 | Package check |
| 2 | Feature check |
| 3 | Configuration check |

**Verification items**

| No. | Verification item | Test |
| --- | --- | --- |
| 1 | Compatibility test | Install, uninstall, commands, services |
| 2 | Basic performance test | Basic benchmark test |
| 3 | Feature test | Feature functional verification |
| 4 | Functional test | Basic AT test |

## 1. Runtime environment

### 1.1. OECP runtime dependencies

| Component | Description | Availability |
| --- | --- | --- |
| python3 | python3.7.9 or above | Check with `yum list` first; download and install if the version is not available |
| sqlite | v3.7.17 or above | Bundled with the system |

## 2. Download, install and deploy oecp

Install abidiff (CentOS): `yum install -y epel-release; yum install -y libabigail`

Install createrepo: `yum install -y createrepo`

Install binutils: `yum install -y binutils`

Install japi:

```
git clone https://github.com/lvc/japi-compliance-checker &&
cd japi-compliance-checker &&
sudo make install prefix=/usr
```

`japi-compliance-checker` depends on the `jar` command (openEuler): `yum install -y java-1.8.0-openjdk-devel`

Note: For openEuler, the openEuler-20.03-SP2 or above `everything` repository needs to be configured.

Install abidiff (openEuler): `yum install -y libabigail`

Install oecp:

```
git clone https://atomgit.com/openeuler/oecp.git;
cd oecp;
pip3 install -r requirement
```

## 3. Usage

```
python3 cli.py [-h] [-n PARALLEL] [-w WORK_DIR] [-p PLAN_PATH]
                [-c CATEGORY_PATH] [--platform PLATFORM_TEST_PATH]
                [-f OUTPUT_FORMAT] [-o OUTPUT_FILE] [-d DEBUGINFO]
                file1 file2
```

* **Positional arguments (required)**
  * **`file`**
    The two ISO files / directories containing rpm packages / rpm packages to compare. Note that `file1` is used as the baseline.

* **Optional arguments**

  * **`-n, --parallel`**
    Number of concurrent processes in the process pool. Default: number of CPU cores.

  * **`-w, --work-dir`**
    Working directory. Default: `/tmp/oecp`.

  * **`-p, --plan`**
    Comparison plan. Default: `'all'` (oecp/conf/plan/all.json).

  * **`-c, --category`**
    Package level information. Default: oecp/conf/category/category.json.

  * **`-d, --debuginfo`**
    Path to the debuginfo iso/rpm.

  * **`-f, --format`**
    Output format. Default: csv.

  * **`-b, --branch`**
    KABI baseline branch. Default: the 20.03-LTS-SP1 branch. Can specify the target kabi whitelist branch for offline comparison (auto-parsed by the tool when the comparison target is an ISO).

  * **`-a, --arch`**
    Architecture to compare. Currently supports x86_64 and aarch64 (auto-parsed by the tool when the architecture is part of the comparison target name).

  * **`-o, --output`**
    Output path of the results. Default: `/tmp/oecp`.

  * **`-r, --rpm-name`**
    Package name of the output. When comparing kernel config files or service files, specify the package name the file belongs to, and configure a `'file'`-type json plan via `-p` according to the file type.

  * **`--platform`**
    Path of the json report for platform verification. Default: `/tmp/oecp`. The default performance baseline file is oecp/conf/performance/openEuler-20.03-LTS-aarch64-dvd.iso.performance.json.

  * **`-s, --src_kernel`**
    Path of the kernel source packages (kernel-*.src.rpm files). Required for kapi comparison mode to look up kapi function prototypes in the kernel source of the corresponding version.

* **Examples**

  * **`python3 cli.py -p kabi /root/openEuler-20.03-LTS-aarch64-dvd.iso /root/openEuler-20.03-LTS-SP1-aarch64-dvd.iso`**

* **Comparison plans**
  * **`all.json`**
    Covers all the comparisons listed below.
  * **`config.json`**
    Compares differences in config file contents inside rpm packages. Requires RPMExtractDumper (the dumper class that extracts rpm packages).
  * **`file_list.json`**
    Compares differences in rpm file lists. The rpm file list can be obtained with `rpm -pql ${rpm_path}`.
  * **`kconfig.json`**
    Compares kernel config files. Requires RPMExtractDumper.
  * **`kabi.json`**
    Compares kernel kabi lists. Requires RPMExtractDumper.
  * **`kapi.json`**
    Captures the kapi prototypes from kabi lists and compares kernel kapi lists. Requires RPMExtractDumper.
  * **`ko.json`**
    Compares modinfo information and interface changes of kernel modules. Requires RPMExtractDumper.
  * **`package_list.json`**
    Compares differences in package name, version, and release between two rpms.
  * **`provides_requires.json`**
    Compares provides/requires differences of rpms, queryable via `rpm -pq --provides/requires ${rpm_path}`.
  * **`abi.json`**
    Compares ABI interface differences of rpm shared library files using the abidiff tool (documentation: https://sourceware.org/libabigail/manual/abidiff.html).
  * **`jabi.json`**
    Compares Java interfaces of jar packages in rpms. Requires RPMExtractDumper.
  * **`service.json`**
    Compares default service configurations of rpms. Requires RPMExtractDumper.
  * **`kabi_file.json`**
    Compares differences in kernel kabi list files. Use this plan (`-p`) when the comparison targets are kernel kabi list files (symvers*).
  * **`kconfig_file.json`**
    Compares differences in kernel config files. Use this plan (`-p`) when the comparison targets are kernel config files (config-*).
  * **`service_file.json`**
    Compares differences in service file configurations. Use this plan (`-p`) when the comparison targets are service files (.service).

## 4. Ascend kabi/kapi baseline function

```
python3 cli.py [-b BRANCH] [-a ARCH] [-s KERNEL_SOURCE] file
```

* **Module description**
  * Extracts kabi lists from one or more driver rpm packages and generates kabi baseline list files. It also supports comparing the driver kabi lists against the community kabi baseline to check whether hardware drivers are compatible with the community OS baseline version.

* **Positional arguments (required)**
  * **Supported types for the `file` argument**
    * File path:
      * Path of a single driver rpm package, e.g., /root/driver_rpm/Ascend-hdk-910-npu-driver-24.1.0-1.aarch64.rpm
      * Driver kabi list file: /root/kabi_list/kabi_list.txt
    * Directory:
      * Directory containing multiple driver rpm packages, e.g., /root/driver_rpm
      * Directory containing multiple ko files, e.g., /root/ko_list

* **Optional arguments**

  * **`-b, --branch`**
    KABI baseline branch. Default: the 20.03-LTS-SP1 branch. Used together with `--arch` to specify the community baseline kabi whitelist, to check whether the extracted driver kabi list matches the OS baseline kabi whitelist.

  * **`-a, --arch`**
    Architecture. Currently supports x86_64 and aarch64. Used together with `--branch` to specify the community baseline kabi whitelist.

  * **`-s, --src_kernel`**
    Path of the kernel source packages (kernel-*.src.rpm files). Adding this argument enables looking up the corresponding kapi function prototypes in the kernel source of the corresponding version.

* **Examples**
  * **`python3 cli.py -b 20.03-LTS-SP1 -a aarch64 -s /root/kernel-5.10.0-rc6.src.rpm /root/driver_rpm/Ascend-hdk-910-npu-driver-24.1.0-1.aarch64.rpm`**

* The generated csv result files are saved under `/tmp/kabi/`.

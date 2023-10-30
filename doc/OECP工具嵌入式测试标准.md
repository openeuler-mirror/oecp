| 项目   | 子项目     | 要求                                            | 验收标准                                                     |
| ------ | ---------- | ----------------------------------------------- | ------------------------------------------------------------ |
| 源码   | 内核       | 必须基于openEuler嵌入式内核                     | 内核版本号一致                                               |
|        |            |                                                 | openEuler嵌入式内核（某个发行版本）的最新commit id在被测代码git中能查询到 |
|        | 基础中间件 | libc保持同openEuler嵌入式一致                   | 版本号一致                                                   |
|        |            |                                                 | openEuler上基础中间件的最新commit id在被测代码git中能查询到  |
|        | 其他软件包 | 如果openEuler社区有，超过70%都选自openEuler社区 | git仓库的remote为gitee.com/src-openeuler或gitee.com/openeuler |
|        |            |                                                 | openEuler嵌入式的基线快照中软件包的commit id可以在被测代码git中查询到 |
| 构建   | 编译器     | 使用openEuler嵌入式的交叉编译器                 | 编译器目录文件MD5一致                                        |
|        | 构建工程   | 使用openEuler嵌入式yocto工程                    | 构建命令一致                                                 |
|        |            |                                                 | 构建目录结构一致                                             |
|        | 包列表     | 构建结束生成的包列表信息和社区一致              | 包列表中70%软件包（社区的软件包）和社区版本一致              |
| 运行时 | 内核       | 内核KABI一致                                    | 白名单内KABI一致，可以增删KABI，但相同的接口必须保持ABI一致。白名单范围为https://gitee.com/src-openeuler/kernel/blob/xxx/kabi_whitelist_XXX。 |
|        | 基础中间件 | libc版本一致                                    | 版本一致，ABI兼容                                            |
|        | 基础功能   | 基础测试通过                                    | 社区AT测试用例测试通过                                       |
|        | POSIX      | 和社区接口保持一致                              | 使用posixtestsuite测试，测试结果和社区一致                   |
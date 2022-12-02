<template>
    <div>
        <table border="1" style="width:100%">
            <tr class="head">
                <td rowspan="2">软件包等级</td>
                <td colspan="5" align="center">服务文件（rpm-service）</td>
                <td colspan="5" align="center">命令文件（rpm-cmd）</td>
                <td colspan="5" align="center">配置文件（rpm-config）</td>
            </tr>
            <tr class="head">
                <td>包变化</td>
                <td>文件增加</td>
                <td>文件减少</td>
                <td>内容一致文件</td>
                <td>内容变化文件</td>
                <td>包变化</td>
                <td>文件增加</td>
                <td>文件减少</td>
                <td>内容一致文件</td>
                <td>内容变化文件</td>
                <td>包变化</td>
                <td>文件增加</td>
                <td>文件减少</td>
                <td>内容一致文件</td>
                <td>内容变化文件</td>
            </tr>
            <tr v-for="row in tables">
                <td>
                    <span v-if="row.rpm_level == 'ALL'">全量软件包</span>
                    <span v-else>{{row.rpm_level}}软件包</span>
                </td>
                <td>
                    <div class="change_view">
                        <div class="lkbtn" @click="handlePkgDetailClick(row, 'rpm-service', 'diff', row.rpm_level)" type="link">
                            {{row['rpm-service_pkg_diff']}}
                        </div>
                        /
                        <div class="lkbtn" @click="handlePkgDetailClick(row,  'rpm-service', 'all', row.rpm_level)" type="link">
                            {{row['rpm-service_pkg_all']}}
                        </div>
                    </div>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm service', 'more')" type="link">
                        {{row["rpm-service_more"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm service', 'less')" type="link">
                        {{row["rpm-service_less"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm service', 'same')" type="link">
                        {{row["rpm-service_same"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm service', 'diff')" type="link">
                        {{row["rpm-service_diff"]}}
                    </a-button>
                </td>
                <td>
                    <div class="change_view">
                        <div class="lkbtn" @click="handlePkgDetailClick(row, 'rpm-cmd', 'diff', row.rpm_level)" type="link">
                            {{row['rpm-cmd_pkg_diff']}}
                        </div>
                        /
                        <div class="lkbtn" @click="handlePkgDetailClick(row,  'rpm-cmd', 'all', row.rpm_level)" type="link">
                            {{row['rpm-cmd_pkg_all']}}
                        </div>
                    </div>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm cmd', 'more')" type="link">
                        {{row["rpm-cmd_more"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm cmd', 'less')" type="link">
                        {{row["rpm-cmd_less"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm cmd', 'same')" type="link">
                        {{row["rpm-cmd_same"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm cmd', 'diff')" type="link">
                        {{row["rpm-cmd_diff"]}}
                    </a-button>
                </td>
                <td>
                    <div class="change_view">
                        <div class="lkbtn" @click="handlePkgDetailClick(row, 'rpm-config', 'diff', row.rpm_level)" type="link">
                            {{row['rpm-config_pkg_diff']}}
                        </div>
                        /
                        <div class="lkbtn" @click="handlePkgDetailClick(row,  'rpm-config', 'all', row.rpm_level)" type="link">
                            {{row['rpm-config_pkg_all']}}
                        </div>
                    </div>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm config', 'more')" type="link">
                        {{row["rpm-config_more"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm config', 'less')" type="link">
                        {{row["rpm-config_less"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm config', 'same')" type="link">
                        {{row["rpm-config_same"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm config', 'diff')" type="link">
                        {{row["rpm-config_diff"]}}
                    </a-button>
                </td>
            </tr>
            <tr class="head">
                <td rowspan="2">软件包等级</td>
                <td colspan="5" align="center">服务文件（rpm-header）</td>
                <td colspan="5" align="center">命令文件（rpm-lib）</td>
                <td colspan="5" align="center">配置文件（rpm-file）</td>
            </tr>
            <tr class="head">
                <td>包变化</td>
                <td>文件增加</td>
                <td>文件减少</td>
                <td>内容一致文件</td>
                <td>内容变化文件</td>
                <td>包变化</td>
                <td>文件增加</td>
                <td>文件减少</td>
                <td>内容一致文件</td>
                <td>内容变化文件</td>
                <td>包变化</td>
                <td>文件增加</td>
                <td>文件减少</td>
                <td>内容一致文件</td>
                <td>内容变化文件</td>
            </tr>
            <tr v-for="row in tables">
                <td>
                    <span v-if="row.rpm_level == 'ALL'">全量软件包</span>
                    <span v-else>{{row.rpm_level}}软件包</span>
                </td>
                <td>
                    <div class="change_view">
                        <div class="lkbtn" @click="handlePkgDetailClick(row, 'rpm-header', 'diff', row.rpm_level)" type="link">
                            {{row['rpm-header_pkg_diff']}}
                        </div>
                        /
                        <div class="lkbtn" @click="handlePkgDetailClick(row,  'rpm-header', 'all', row.rpm_level)" type="link">
                            {{row['rpm-header_pkg_all']}}
                        </div>
                    </div>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm header', 'more')" type="link">
                        {{row["rpm-header_more"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm header', 'less')" type="link">
                        {{row["rpm-header_less"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm header', 'same')" type="link">
                        {{row["rpm-header_same"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm header', 'diff')" type="link">
                        {{row["rpm-header_diff"]}}
                    </a-button>
                </td>
                <td>
                    <div class="change_view">
                        <div class="lkbtn" @click="handlePkgDetailClick(row, 'rpm-lib', 'diff', row.rpm_level)" type="link">
                            {{row['rpm-lib_pkg_diff']}}
                        </div>
                        /
                        <div class="lkbtn" @click="handlePkgDetailClick(row,  'rpm-lib', 'all', row.rpm_level)" type="link">
                            {{row['rpm-lib_pkg_all']}}
                        </div>
                    </div>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm lib', 'more')" type="link">
                        {{row["rpm-lib_more"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm lib', 'less')" type="link">
                        {{row["rpm-lib_less"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm lib', 'same')" type="link">
                        {{row["rpm-lib_same"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm lib', 'diff')" type="link">
                        {{row["rpm-lib_diff"]}}
                    </a-button>
                </td>
                <td>
                    <div class="change_view">
                        <div class="lkbtn" @click="handlePkgDetailClick(row, 'rpm-file', 'diff', row.rpm_level)" type="link">
                            {{row['rpm-file_pkg_diff']}}
                        </div>
                        /
                        <div class="lkbtn" @click="handlePkgDetailClick(row,  'rpm-file', 'all', row.rpm_level)" type="link">
                            {{row['rpm-file_pkg_all']}}
                        </div>
                    </div>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm files', 'more')" type="link">
                        {{row["rpm-file_more"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm files', 'less')" type="link">
                        {{row["rpm-file_less"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm files', 'same')" type="link">
                        {{row["rpm-file_same"]}}
                    </a-button>
                </td>
                <td>
                    <a-button @click="handleDetailClick(row, 'rpm files', 'diff')" type="link">
                        {{row["rpm-file_diff"]}}
                    </a-button>
                </td>
            </tr>
        </table>
    </div>
</template>

<script>
export default {
    name: 'tables_page',
    props:{
        report_base_id: {
            type: String|Number,
            default: ''
        }
    },
    data () {
        return {
            loading: false,
            tables: []
        }
    },
    computed: {
    },
    mounted() {
        var self = this
        this.$nextTick(()=>{
            self.getData()
        })
    },
    methods: {
        /** 数据详情 */
        handleDetailClick(row, c_type, c_result){
            var self = this
            let c_level = ''
            if(row.rpm_level == 'L1') {
                c_level = 1
            } else if(row.rpm_level == 'L2'){
                c_level = 2
            }
            this.$router.push({name: 'file_report', query: {
                    report_base_id: self.report_base_id,
                    level: c_level,
                    c_type: c_type,
                    c_result: c_result
                }
            })
        },
        /** 包变化 */
        handlePkgDetailClick(row, c_type, c_result, level){
            var self = this
            let c_level = ''
            if(level == 'L1') {
                c_level = 1
            } else if(level == 'L2'){
                c_level = 2
            }
            let type = ''
            if(c_type == 'rpm-service'){
                type = 'rpm service'
            }
            if(c_type == 'rpm-cmd'){
                type = 'rpm cmd'
            }
            if(c_type == 'rpm-config'){
                type = 'rpm config'
            }
            if(c_type == 'rpm-header'){
                type = 'rpm header'
            }
            if(c_type == 'rpm-lib'){
                type = 'rpm lib'
            }
            if(c_type == 'rpm-file'){
                type = 'rpm files'
            }
            this.$router.push({name: 'all_rpm_report', query: {
                    r_bid: self.report_base_id,
                    a_type: c_result,
                    c_type: type,
                    c_level: c_level
                }
            })
        },
        getData () {
            var self = this
            self.loading = true
            // self.$http.get(`statistical/detail/rpm-service-cmd-conf/${self.report_base_id}`).then(res=>{
            self.$http.get(`statistical/detail/rpmfile-analyse/${self.report_base_id}`).then(res=>{
                self.loading = false
                let data = [{},{},{}]
                res.data.data.forEach((item, index)=>{
                    let _t = item.rpm_type
                    let _pkg_all = item.package_change.split('/')[1]
                    let _pkg_diff = item.package_change.split('/')[0]
                    let _index = 0
                    if(item.rpm_level == 'ALL'){
                        _index = 0
                    } else if(item.rpm_level == 'L1') {
                        _index = 1
                    } else if(item.rpm_level == 'L2') {
                        _index = 2
                    }
                    self.$set(data[_index],  `${_t}_pkg_all`, _pkg_all)
                    self.$set(data[_index],  `${_t}_pkg_diff`, _pkg_diff)
                    self.$set(data[_index],  `rpm_level`, item.rpm_level)
                    self.$set(data[_index],  `${_t}_more`, item.file_more)
                    self.$set(data[_index],  `${_t}_less`, item.file_less)
                    self.$set(data[_index],  `${_t}_same`, item.file_consistent)
                    self.$set(data[_index],  `${_t}_diff`, item.file_content_change)
                })
                console.log('data', data)
                this.tables = JSON.parse(JSON.stringify(data))
                this.total = res.data.data.total
            },error=>{
              self.loading = false
            })
        },
    }
}
</script>

<style lang="less" scoped>
    .change_view{
        display: flex;
        .lkbtn{
            color: #3e8bfe;
            cursor: pointer;
            padding: 0 5px;
        }
    }

    
table{
    border: 1px solid #e8e8e8;
    line-height: 55px;
    color: #555770;
    font-size: 14px;
    tr{
        &.head{
            background: #fafafa;
        }
        td{
            padding: 0 16px;
            &.pass{
                background: rgba(82, 196, 26, 0.1);
            }
            &.no_pass{
                background: rgba(226, 91, 114, 0.1);
            }
        }
    }
}
</style>

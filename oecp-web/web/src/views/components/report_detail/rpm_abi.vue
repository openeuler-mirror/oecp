<template>
    <div>
        <a-table :data-source="tables" :columns="columns" :rowKey="(record, index) => { return index}" :pagination="false" :expandRowByClick="true" :loading="loading" bordered>
            <template slot="index" slot-scope="text, row, index">
                <span>{{(pageIndex - 1) * pageSize + index + 1}}</span>
            </template>
            <template slot="level" slot-scope="text, row">
                <span v-if="row.rpm_level == 'ALL'">全量软件包</span>
                <span v-else>{{row.rpm_level}}软件包</span>
            </template>
            <template slot="package_change" slot-scope="text, row">
                <div class="change_view">
                    <div class="lkbtn" @click="handlePkgDetailClick(row, 'rpm-abi', 'diff', row.rpm_level)" type="link">
                        {{row.pkg_diff}}
                    </div>
                    /
                    <div class="lkbtn" @click="handlePkgDetailClick(row,  'rpm-abi', 'all', row.rpm_level)" type="link">
                        {{row.pkg_all}}
                    </div>
                </div>
            </template>
            <template slot="less" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'rpm abi', 'less')" type="link">
                    {{row.file_less}}
                </a-button>
            </template>
            <template slot="diff" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'rpm abi', 'less')" type="link">
                    {{row.file_content_change}}
                </a-button>
            </template>
            <template slot="more" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'rpm abi', 'less')" type="link">
                    {{row.file_more}}
                </a-button>
            </template>
            <template slot="actions" slot-scope="text, row">
                <a-space>
                <a-button type="primary" @click="handleReportDetail(row)">查看详情</a-button>
                <a-button type="danger" >删除</a-button>
                </a-space>
            </template>
        </a-table>
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
            columns: [
                {title: '软件包等级', key: 'level',scopedSlots: {customRender :'level'}, dataIndex: 'level'},
                {title: '包变化',dataIndex: 'package_change',scopedSlots: {customRender :'package_change'}},
                {title: '接口删除', key: 'file_less', dataIndex: 'file_less'},
                {title: '接口变化', key: 'file_content_change', dataIndex: 'file_content_change'},
                {title: '新增接口', key: 'file_more', dataIndex: 'file_more'},
            ],
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
            this.$router.push({name: 'all_rpm_report', query: {
                    r_bid: self.report_base_id,
                    a_type: c_result,
                    c_type: 'rpm abi',
                    c_level: c_level
                }
            })
        },
        getData () {
            var self = this
            self.loading = true
            self.$http.get(`statistical/detail/rpmfile-analyse/${self.report_base_id}?type=rpm-abi`).then(res=>{
                self.loading = false
                let list = []
                res.data.data.forEach((item, index)=>{
                    let _pkg_all = item.package_change.split('/')[1]
                    let _pkg_diff = item.package_change.split('/')[0]
                    self.$set(item,  `pkg_all`, _pkg_all)
                    self.$set(item,  `pkg_diff`, _pkg_diff)
                    if(item.rpm_type == 'rpm-abi'){
                        list.push(item)
                    }
                })
                this.tables = JSON.parse(JSON.stringify(list))
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

</style>

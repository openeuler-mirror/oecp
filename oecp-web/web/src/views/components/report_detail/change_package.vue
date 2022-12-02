<template>
    <div>
        <a-table :data-source="tables" :columns="columns" :rowKey="(record, index) => { return index}" :pagination="false" :expandRowByClick="true" :loading="loading" bordered>
            <template slot="index" slot-scope="text, row, index">
                <span>{{(pageIndex - 1) * pageSize + index + 1}}</span>
            </template>
            <template slot="level" slot-scope="text, row">
                <span v-if="row.level == 'ALL'">全量软件包</span>
                <span v-else>{{row.level}}软件包</span>
            </template>
            <template slot="r_delete" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'r_delete')" type="link">
                    {{text}}
                </a-button>
            </template>
            <template slot="r_add" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'r_add')" type="link">
                    {{text}}
                </a-button>
            </template>
            <template slot="r_release" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'r_release')" type="link">
                    {{text}}
                </a-button>
            </template>
            <template slot="version_update" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'version_update')" type="link">
                    {{text}}
                </a-button>
            </template>
            <template slot="consistent" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'consistent')" type="link">
                    {{text}}
                </a-button>
            </template>
            <template slot="provide_change" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'provide_change')" type="link">
                    {{text}}
                </a-button>
            </template>
            <template slot="require_change" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, 'require_change')" type="link">
                    {{text}}
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
                {title: '软件包', key: 'level',scopedSlots: {customRender :'level'}, dataIndex: 'level'},
                {title: '删除', key: 'r_delete',scopedSlots: {customRender :'r_delete'}, dataIndex: 'r_delete'},
                {title: '新增', key: 'r_add',scopedSlots: {customRender :'r_add'}, dataIndex: 'r_add'},
                {title: 'release', key: 'r_release',scopedSlots: {customRender :'r_release'}, dataIndex: 'r_release'},
                {title: '版本升级', key: 'version_update',scopedSlots: {customRender :'version_update'}, dataIndex: 'version_update'},
                {title: '保持一致', key: 'consistent',scopedSlots: {customRender :'consistent'}, dataIndex: 'consistent'},
                {title: 'provide变化', key: 'provide_change',scopedSlots: {customRender :'provide_change'}, dataIndex: 'provide_change'},
                {title: 'require变化', key: 'require_change',scopedSlots: {customRender :'require_change'}, dataIndex: 'require_change'},
            ],
            tables: [
                // {level: '全量软件包', provide_change: 1, consistent: 10, diff: 10, r_delete: 20, r_add: 13, r_release: 15, version_update: 156, require_change: 17},
                // {level: 'L1软件包', provide_change: 2, consistent: 10, diff: 10, r_delete: 20, r_add: 13, r_release: 7, version_update: 42, require_change: 3},
                // {level: 'L2软件包', provide_change: 3, consistent: 10, diff: 10, r_delete: 20, r_add: 13, r_release: 9, version_update: 13, require_change: 6},
            ]
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
        handleDetailClick(row, type){
            let c_level = ''
            if(row.level == 'L1') {
                c_level = 1
            } else if(row.level == 'L2'){
                c_level = 2
            }
            let c_type = 'rpm package name'
            if(type == 'provide_change') {
                c_type = 'rpm provides'
            }
            if(type == 'require_change'){
                c_type = 'rpm requires'
            }
            this.$router.push({name: 'all_rpm_report', query:{
                r_bid: this.report_base_id,
                a_type: type,
                c_type: c_type,
                c_level: c_level
            }})
        },
        getData () {
            var self = this
            self.loading = true
            self.$http.get(`statistical/detail/all-package/${self.report_base_id}`).then(res=>{
                self.loading = false
                this.tables = JSON.parse(JSON.stringify(res.data.data))
                this.total = res.data.data.total
            },error=>{
              self.loading = false
            })
        },
    }
}
</script>

<style lang="less" scoped>
</style>

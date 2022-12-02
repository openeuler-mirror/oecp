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
            <template slot="file_more" slot-scope="text, row">
                {{row.file_more}}
            </template>
            <template slot="file_less" slot-scope="text, row">
                {{row.file_less}}
            </template>
            <template slot="file_consistent" slot-scope="text, row">
                {{row.file_consistent}}
            </template>
            <template slot="file_content_change" slot-scope="text, row">
                {{row.file_content_change}}
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
        },
        r_type: {
            type: String,
            default: ''
        },
        r_type_text: {
            type: String,
            default: ''
        },
    },
    data () {
        return {
            loading: false,
            // r_type_text: '',
            columns: [
                {title: `软件包等级`, key: 'level',scopedSlots: {customRender :'level'}, dataIndex: 'level'},
                {title: '包变化', dataIndex: 'package_change', key: 'package_change'},
                {title: `${this.r_type_text}文件增加`, scopedSlots: {customRender :'file_more'}, key: 'file_more'},
                {title: `${this.r_type_text}文件减少`, scopedSlots: {customRender :'file_less'}, key: 'file_less'},
                {title: `内容一致${this.r_type_text}文件`, scopedSlots: {customRender :'file_consistent'}, key: 'file_consistent'},
                {title: `${this.r_type_text}文件内容变化`, scopedSlots: {customRender :'file_content_change'}, key: 'file_content_change'},
            ],
            tables: []
        }
    },
    computed: {
    },
    created(){
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
            } else if(this.level == 'L2'){
                c_level = 2
            }
            let c_type = 'rpm files'; // rpm header; rpm lib
            if(this.r_type == 'rpm-header') {
                c_type = 'rpm header'
            }
            if(this.r_type == 'rpm-lib'){
                c_type = 'rpm lib'
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
            self.$http.get(`statistical/detail/rpmfile-analyse/${self.report_base_id}?type=${self.r_type}`).then(res=>{
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

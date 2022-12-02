<template>
    <div>
        <a-table :data-source="tables" :columns="columns" :rowKey="(record, index) => { return index}" :pagination="false" :expandRowByClick="true" :loading="loading" bordered>
            <template slot="more" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, row.kernel_analyse, 'more')" type="link">
                    {{row.more}}
                </a-button>
            </template>
            <template slot="less" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, row.kernel_analyse, 'less')" type="link">
                    {{row.less}}
                </a-button>
            </template>
            <template slot="same" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, row.kernel_analyse, 'same')" type="link">
                    {{row.same}}
                </a-button>
            </template>
            <template slot="diff" slot-scope="text, row">
                <a-button @click="handleDetailClick(row, row.kernel_analyse, 'diff')" type="link">
                    {{row.diff}}
                </a-button>
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
                {title: 'Kernel-Analyse', key: 'kernel_analyse', dataIndex: 'kernel_analyse'},
                {title: 'more result', key: 'more', scopedSlots: {customRender :'more'}},
                {title: 'less result', key: 'less', scopedSlots: {customRender :'less'}},
                {title: 'same result', key: 'same', scopedSlots: {customRender :'same'}},
                {title: 'diff result', key: 'diff', scopedSlots: {customRender :'diff'}},
            ],
            tables: [
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
        /** 数据详情 */
        handleDetailClick(row, c_type, c_result){
            var self = this
            let type = ''
            if(c_type == 'driver kconfig'){
                type = 'drive kconfig'
            } else if(c_type == 'driver kabi'){
                type = 'drive kabi'
            } else{
                type = c_type
            }
            this.$router.push({name: 'file_report', query: {
                    report_base_id: self.report_base_id,
                    level: '',
                    c_type: type,
                    c_result: c_result
                }
            })
        },
        getData () {
            var self = this
            self.loading = true
            self.$http.get(`statistical/detail/kernel-analyse/${self.report_base_id}`).then(res=>{
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

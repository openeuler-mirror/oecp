<template>
    <div>
        <a-table :data-source="tables" :columns="columns" :rowKey="(record, index) => { return index}" :pagination="false" :expandRowByClick="true" :loading="loading">
            <template slot="weight" slot-scope="text, row, index">
                <span>{{text}}%</span>
            </template>
            <template slot="value" slot-scope="text, row, index">
                <span>{{text}}%</span>
            </template>
        </a-table>
    </div>
</template>

<script>
export default {
    name: 'tables_page',
    props:{
        report_base_id: {
            type: String | Number,
            default: ''
        }
    },
    data () {
        return {
            loading: false,
            columns: [
                {title: '测试项', key: 'test_item', dataIndex: 'test_item'},
                {title: '权重', key: 'weight', scopedSlots: {customRender :'weight'}, dataIndex: 'weight'},
                {title: '单项得分值', key: 'value', scopedSlots: {customRender :'value'}, dataIndex: 'value'}
            ],
            tables: [
                {test_item: '软件包范围', weight: 20, value: 13},
                {test_item: '软件包相似度', weight: 20, value: 13},
                {test_item: '软件包依赖关系', weight: 20, value: 13},
                {test_item: '合计', weight: 0, value: 13},
            ]
        }
    },
    mounted() {
        var self = this
        this.$nextTick(()=>{
            // self.getData()
        })
    },
    
    methods: {
        getData () {
            var self = this
            self.loading = true
            self.$http.get(`report/detail/all-result/${self.report_base_id}`).then(res=>{
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

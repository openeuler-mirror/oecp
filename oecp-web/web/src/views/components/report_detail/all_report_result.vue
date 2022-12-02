<template>
    <div>
        <a-table :data-source="tables" :columns="columns" :rowKey="(record, index) => { return index}" :pagination="false" :expandRowByClick="true" :loading="loading" bordered>
            <template slot="index" slot-scope="text, row, index">
                <span>{{(pageIndex - 1) * pageSize + index + 1}}</span>
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
                {title: 'category level', key: 'category', dataIndex: 'category'},
                {title: 'same', key: 'same', dataIndex: 'same'},
                {title: 'diff', key: 'diff', dataIndex: 'diff'},
                {title: 'less', key: 'less', dataIndex: 'less'},
                {title: 'more', key: 'more', dataIndex: 'more'}
            ],
            tables: [
                {category: 1, same: 10, diff: 10, less: 20, more: 13},
                {category: 2, same: 10, diff: 10, less: 20, more: 13},
                {category: 3, same: 10, diff: 10, less: 20, more: 13},
                {category: 4, same: 10, diff: 10, less: 20, more: 13},
                {category: 5, same: 10, diff: 10, less: 20, more: 13},
            ]
        }
    },
    mounted() {
        var self = this
        this.$nextTick(()=>{
            self.getData()
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

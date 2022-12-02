<template>
    <div>
        <table border="1" style="width:100%">
            <tr>
                <td colspan="3" align="center">Compatible</td>
                <td>OSV 版本</td>
                <td colspan="2">
                    {{osv_form.osv_version}}
                </td>
            </tr>
            <tr>
                <td colspan="3" rowspan="4" align="center">
                    <!-- {{osv_form.detection_result}} -->
                    
                    <div v-if="osv_form.detection_result=='不通过'" class="r_dispass">不通过</div>
                    <div v-else class="r_pass">{{osv_form.detection_result}}</div>
                </td>
                <td>架构</td>
                <td colspan="2">{{osv_form.architecture}}</td>
            </tr>
            <tr>
                <td>发布地址</td>
                <td colspan="2">{{osv_form.release_addr}}</td>
            </tr>
            <tr>
                <td>checksum</td>
                <td colspan="2">{{osv_form.checksum}}</td>
            </tr>
            <tr>
                <td>基于openEuler的版本</td>
                <td colspan="2">{{osv_form.base_home_old_ver}}</td>
            </tr>
            <tr class="head">
                <td>测评维度</td>
                <td>检测项</td>
                <td>检测点描述</td>
                <td colspan="2">测试结果</td>
                <td>结论</td>
            </tr>
            <template v-for="item in osv_form.items">
                <tr v-for="(itm, idx) in item.test_items" :key="idx">
                    <td v-if="idx == 0" :rowspan="item.test_items.length" align="center">{{item.dimension}}</td>
                    <td>{{itm.test_item}}</td>
                    <td>{{itm.describe}}</td>
                    <td colspan="2" align="center">{{itm.test_result}}</td>
                    <td :class="[itm.conclusion == 'PASS' ? 'pass' :'no_pass']">{{itm.conclusion}}</td>
                </tr>
            </template>
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
            osv_form: {}
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
        getData () {
            var self = this
            self.loading = true
            self.$http.get(`report/detail/osv/${self.report_base_id}`).then(res=>{
                self.loading = false
                var _osv_form = {
                    ...res.data.data,
                    items: JSON.parse(res.data.data.detail_json)
                }
                console.log(_osv_form)
                // _osv_form.detection_result = '通过'
                this.osv_form = _osv_form
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
.r_pass {
    display: inline-block;
    width: 100%;
    height: 100%;
    
    color: #52c41a;
    font-weight: bold;
    font-size: 20px;
}
.r_dispass{
    display: inline-block;
    width: 100%;
    height: 100%;
    color: #ff4d4f;
    font-weight: bold;
    font-size: 20px;
}
</style>

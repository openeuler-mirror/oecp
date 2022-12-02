<template>
    <div>
      <div class="echart_card">
          <div class="echart_title"><slot name="title"></slot></div>
          <mx-echart ref="chart3" chart_ref="myChart_3" :options="options"></mx-echart>
      </div>
    </div>
  </template>
  
  <script>
import mxEchart from '@/components/mx-echart/index.vue'
export default {
    name: 'tables_page',
    components: {
        mxEchart
    },
    props:{
        r_id:''
    },
    data () {
        return {
            loading: false,
            rpm_type: 'rpm-package',
            options: {
            },
        }
    },
    methods: {
        /**
         * 构造软件包图表数据
         */
        init_chart_data(rows) {
            var _series = []
            var _series_data = []
            rows.forEach(item=>{
                _series_data.push(
                    [
                        { name: '删除', itemStyle:{color:'#ee6666'}, value: parseInt(item.r_delete)},
                        { name: '新增', itemStyle:{color:'#3ba272'}, value: parseInt(item.r_add)},
                        { name: 'release', itemStyle:{color:'#73c0de'}, value: parseInt(item.r_release)},
                        { name: '版本升级', itemStyle:{color:'#91cc75'}, value: parseInt(item.version_update)},
                        { name: '保持一致', itemStyle:{color:'#fac858'}, value: parseInt(item.consistent)},
                        { name: 'provide变化', itemStyle:{color:'#fc8452'}, value: parseInt(item.provide_change)},
                        { name: 'require变化', itemStyle:{color:'#ea7ccc'}, value: parseInt(item.require_change)},
                    ]
                )
            })
            if(rows.length == 0){
                _series=[
                    { name: '', type: 'bar', label:{ show: true, formatter: '{c}', position: 'outer' }, data: []},
                ]
            } else {
                _series.push({ 
                    labelLayout:{
                        dx: 0,
                        dy: 120,
                    },
                    name: '全量软件包', type: 'pie', radius: ['50%', '70%'], label: { position: 'center', formatter:'{a}', fontSize: 14 }, data: _series_data[0]})
                _series.push({
                    labelLayout:{
                        dx: 0,
                        dy: 70,
                    },
                    name: 'L1软件包', type: 'pie', radius: ['25%', '45%'], label: { position: 'center', formatter:'{a}', fontSize: 14, show: true}, labelLine: { show: false }, data: _series_data[1]})
                _series.push({ name: 'L2软件包', type: 'pie', radius: [0, '20%'], label: { position: 'center', formatter:'{a}', fontSize: 14, show: true }, labelLine: { show: false }, data: _series_data[2]})
            }
            console.log('series——pie', _series)
            this.options = {
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c} ({d}%)'
                },
                grid: {
                    top: '10%',
                    left: '50px',
                    right: '50px',
                    bottom: '15%',
                    containLabel: true
                },
                legend: {
                    bottom: 10,
                },
                series: JSON.parse(JSON.stringify(_series))
            }
        },
        init_data(){
            this.init_package_data()
        },
        init_package_data(){
            var self = this
            self.loading = true
            self.$http.get(`statistical/detail/all-package/${self.r_id}`).then(res=>{
                self.loading = false
                var rows = JSON.parse(JSON.stringify(res.data.data))
                self.init_chart_data(rows)
            },error=>{
                self.loading = false
            })
        },
        onresize(){
            this.$refs["chart3"].resize()
        }
    },
}
</script>

<style lang="less" scoped>
.action{
    position: absolute;
    background: #ffffff;
    // padding: 10px;
    top: 4px;
    right: 20px;
}
</style>

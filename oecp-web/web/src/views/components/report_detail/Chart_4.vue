<template>
    <div>
      <div class="echart_card">
          <div class="echart_title"><slot name="title"></slot></div>
          <mx-echart ref="chart4" chart_ref="myChart_4" :options="options"></mx-echart>
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
            options: {},
        }
    },
    methods: {
        /**
         * 构造软件包图表数据
         * @param {*} level 软件包等级 
         * @param {*} rows 选中的软件包数据
         */
        on_data_change(rows, x_axis_data, y_axis_title_data) {
            var _series = []
            var _array_delete = []
            var _array_add = []
            var _array_consistent = []
            var _array_change = []
            rows.forEach(item=>{
                _array_add.push(parseInt(item.more))
                _array_delete.push(parseInt(item.less))
                _array_consistent.push(parseInt(item.same))
                _array_change.push(parseInt(item.diff))
            })
            if(rows.length == 0){
                _series=[
                    { name: '', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: []},
                ]
            } else {
                _series = [
                    { name: 'more', stack: 'total', itemStyle:{color:'#3ba272'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_add},
                    { name: 'less', stack: 'total', itemStyle:{color:'#ee6666'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_delete},
                    { name: 'same', stack: 'total', itemStyle:{color:'#fac858'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_consistent},
                    { name: 'diff', stack: 'total', itemStyle:{color:'#fc8452'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_change},
                ]
            }
            console.log('series2', _series)
            this.options = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                legend: {
                    bottom: 10,
                },
                grid: {
                    top: '10%',
                    left: '50px',
                    right: '50px',
                    bottom: '15%',
                    containLabel: true
                },
                xAxis: {
                    type: 'value',
                },
                yAxis: [
                    {
                        type: 'category',
                        data: ['driver kabi', 'driver kconfig', 'kabi', 'kconfig']
                    }
                ],
                series: JSON.parse(JSON.stringify(_series))
            }
        },
        init_data(){
            this.init_kernel_data()
        },
        init_kernel_data(){
            var self = this
            self.loading = true
            self.$http.get(`statistical/detail/kernel-analyse/${self.r_id}`).then(res=>{
                self.loading = false
                var rows = JSON.parse(JSON.stringify(res.data.data))
                self.on_data_change(rows)
            },error=>{
                self.loading = false
            })
        },
        onresize(){
            this.$refs["chart4"].resize()
        }
    },
}
</script>

<style lang="less" scoped>
.action{
    position: absolute;
    background: #ffffff;
    // padding: 10px;
    top: 44px;
    right: 20px;
}
</style>

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
            options: {},
            default_options: {
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
                yAxis: [
                    {
                        type: 'value'
                    }
                ],
            }
        }
    },
    methods: {
        /**
         * 构造软件包图表数据
         * @param {*} level 软件包等级 
         * @param {*} rows 选中的软件包数据
         */
         init_chart_data(rows, x_axis_data, y_axis_title_data) {
            var x_axis_data = []
            var _series = []
            var _array_same = []
            var _array_diff = []
            var _array_less = []
            var _array_more = []
            rows.forEach(item=>{
                x_axis_data.push('category level ' + item.category)
                _array_same.push(parseInt(item.same))
                _array_diff.push(parseInt(item.diff))
                _array_less.push(parseInt(item.less))
                _array_more.push(parseInt(item.more))
            })
            if(rows.length == 0){
                _series=[
                    { name: '', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: []},
                ]
            } else {
                _series = [
                    { name: 'same', itemStyle:{color:'#ee6666'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_same},
                    { name: 'diff', itemStyle:{color:'#3ba272'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_diff},
                    { name: 'less', itemStyle:{color:'#73c0de'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_less},
                    { name: 'more', itemStyle:{color:'#91cc75'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_more}
                ]
            }
            console.log('series2', _series)
            this.options = {
                ...this.default_options,
                xAxis: [
                    {
                        type: 'category',
                        axisTick: { show: false },
                        data: x_axis_data
                    }
                ],
                series: JSON.parse(JSON.stringify(_series))
            }
        },
        init_data(){
            this.init_result_data()
        },
        init_result_data(){
            var self = this
            self.loading = true
            self.$http.get(`report/detail/all-result/${self.r_id}`).then(res=>{
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
</style>

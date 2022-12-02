<template>
  <div>
    <div class="echart_card">
        <div class="echart_title"><slot name="title"></slot></div>
        <mx-echart ref="chart2" chart_ref="myChart_2" :options="options"></mx-echart>
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
        search_form: {
            type: Object,
            default: ()=>{}
        }
    },
    data () {
        return {
            options: {
            }
        }
    },
    methods: {
        /**
         * 构造软件包图表数据
         * @param {*} level 软件包等级 
         * @param {*} rows 选中的软件包数据
         */
        on_data_change(rows) {
            var _series = []
            var _x_axis_data = []
            var _array_delete = []
            var _array_add = []
            var _array_release = []
            var _array_version_update = []
            var _array_consistent = []
            var _array_provide_change = []
            var _array_require_change = []
            rows.forEach(item=>{
                _array_delete.push(parseInt(item.r_delete))
                _array_add.push(parseInt(item.r_add))
                _array_release.push(parseInt(item.r_release))
                _array_version_update.push(parseInt(item.version_update))
                _array_consistent.push(parseInt(item.consistent))
                _array_provide_change.push(parseInt(item.provide_change))
                _array_require_change.push(parseInt(item.require_change))
                _x_axis_data.push(
                    {value: item.version, 
                    // textStyle: {
                    //     overflow:'truncate',
                    //     width: 100,
                    //     ellipsis: '...'
                    // },
                })
            })
            if(rows.length == 0){
                _series=[
                    { name: '', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: []},
                ]
            } else {
                    _series = [
                        { itemStyle:{color:'#ee6666'}, name: '删除', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_delete},
                        { itemStyle:{color:'#3ba272'}, name: '新增', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_add},
                        { itemStyle:{color:'#73c0de'}, name: 'release', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_release},
                        { itemStyle:{color:'#91cc75'}, name: '版本升级', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_version_update},
                        { itemStyle:{color:'#fac858'}, name: '保持一致', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_consistent},
                        { itemStyle:{color:'#fc8452'}, name: 'provide变化', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_provide_change},
                        { itemStyle:{color:'#ea7ccc'}, name: 'require变化', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_require_change},
                    ]
            }
            console.log('series_index_2', _series)
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
                    top: '3%',
                    left: '3%',
                    right: '4%',
                    bottom: '10%',
                    containLabel: true
                },
                xAxis: [
                    {
                        type: 'category',
                        axisTick: { show: false },
                        data: _x_axis_data
                    }
                ],
                yAxis: [
                    {
                        type: 'value'
                    }
                ],
                series: JSON.parse(JSON.stringify(_series))
            }
        },
        onresize(){
            this.$refs["chart2"].resize()
        }
    },
}
</script>

<style lang="less" scoped>

</style>

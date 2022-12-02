<template>
  <div>
    <div class="echart_card">
        <div class="echart_title"><slot name="title"></slot></div>
        <mx-echart ref="chart1" chart_ref="myChart_1" :options="options"></mx-echart>
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
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow' // 'shadow' as default; can also be 'line' or 'shadow'
                    },
                    // formatter: '{a0}: {c0}% <br />{a1}: {c1}%<br />{a2}: {c2}%<br />{a3}: {c3}%'
                },
                legend: {
                    bottom: 10
                },
                grid: {
                    top: '3%',
                    left: '4%',
                    right: '5%',
                    bottom: '10%',
                    containLabel: true
                },
                xAxis: {
                    type: 'value'
                },
                yAxis: {
                    type: 'category',
                    data: ['删除', '新增', 'release', '版本升级', '保持一致', 'provide变化', 'require变化']
                },
                // series: [
                //     {
                //         name: '6.8VS7.6',
                //         type: 'bar',
                //         stack: 'total',
                //         label: {
                //             show: true,
                //             formatter: '{c}%',
                //         },
                //         emphasis: {
                //             focus: 'series'
                //         },
                //         data: [30, 40, 10, 20, 30, 60, 20]
                //     },
                //     {
                //         name: '7.6VS8.2',
                //         type: 'bar',
                //         stack: 'total',
                //         label: {
                //             show: true,
                //             formatter: '{c}%',
                //         },
                //         emphasis: {
                //             focus: 'series'
                //         },
                //         data: [60, 30, 20, 30, 10, 10, 70]
                //     },
                //     {
                //         name: '7.6VS7.7',
                //         type: 'bar',
                //         stack: 'total',
                //         label: {
                //             show: true,
                //             formatter: '{c}%',
                //         },
                //         emphasis: {
                //             focus: 'series'
                //         },
                //         data: [10, 30, 70, 50, 60, 30, 10]
                //     }
                // ]
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
            var _total_delete = 0
            var _total_add = 0
            var _total_release = 0
            var _total_version_update = 0
            var _total_consistent = 0
            var _total_provide_change = 0
            var _total_require_change = 0
            rows.forEach(item=>{
                _total_delete += parseInt(item.r_delete)
                _total_add += parseInt(item.r_add)
                _total_release += parseInt(item.r_release)
                _total_version_update += parseInt(item.version_update)
                _total_consistent += parseInt(item.consistent)
                _total_provide_change += parseInt(item.provide_change)
                _total_require_change += parseInt(item.require_change)
            })
            if(rows.length == 0){
                _series=[
                    {
                        name: '',
                        type: 'bar',
                        stack: 'total',
                        label: {
                            show: true,
                            formatter: '{c}%',
                        },
                        emphasis: {
                            focus: 'series'
                        },
                        data: []
                    }
                ]
            } else {
                rows.forEach(item=>{
                    var r_delete = item.r_delete ? parseInt(item.r_delete) : 0
                    var r_add = item.r_add ? parseInt(item.r_add) : 0
                    var r_release = item.r_release ? parseInt(item.r_release) : 0
                    var version_update = item.version_update ? parseInt(item.version_update) : 0
                    var consistent = item.consistent ? parseInt(item.consistent) : 0
                    var provide_change = item.provide_change ? parseInt(item.provide_change) : 0
                    var require_change = item.require_change ? parseInt(item.require_change) : 0
                    _series.push(
                        {
                            name: item.version,
                            type: 'bar',
                            stack: 'total',
                            label: {
                                show: true,
                                formatter: '{c}%',
                            },
                            // emphasis: {
                            //     focus: 'series'
                            // },
                            data: [Math.round(r_delete * 100 / _total_delete), Math.round(r_add * 100 / _total_add), Math.round(r_release * 100 / _total_release), 
                            Math.round(version_update * 100 / _total_version_update), Math.round(consistent * 100 / _total_consistent), Math.round(provide_change * 100 / _total_provide_change), Math.round(require_change * 100 / _total_require_change)]
                        }
                    )
                })
            }
            console.log('series1', _series)
            this.options = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow' // 'shadow' as default; can also be 'line' or 'shadow'
                    },
                    // formatter: '{a0}: {c0}% <br />{a1}: {c1}%<br />{a2}: {c2}%<br />{a3}: {c3}%'
                },
                legend: {
                    bottom: 10
                },
                grid: {
                    top: '3%',
                    left: '4%',
                    right: '5%',
                    bottom: '10%',
                    containLabel: true
                },
                xAxis: {
                    type: 'value'
                },
                yAxis: {
                    type: 'category',
                    data: ['删除', '新增', 'release', '版本升级', '保持一致', 'provide变化', 'require变化']
                },
                series: _series
            }
        },
        onresize(){
            this.$refs["chart1"].resize()
        }
    },
}
</script>

<style lang="less" scoped>

</style>

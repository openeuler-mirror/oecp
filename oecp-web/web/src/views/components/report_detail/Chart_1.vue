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
        r_id:''
    },
    data () {
        return {
            loading: false,
            options: {
            }
        }
    },
    methods: {
        /**
         * 构造软件包图表数据
         */
         init_chart_data(rows) {
            var _indicators = []
            var _series = []
            let _sames = []
            let _diffs = []
            let _lesses = []
            let _mores = []
            rows.forEach(item=>{
                _sames.push(parseInt(item.same))
                _diffs.push(parseInt(item.diff))
                _lesses.push(parseInt(item.less))
                _mores.push(parseInt(item.more))
                let _max = 0
                if(parseInt(item.same) > _max){
                    _max = parseInt(item.same)
                }
                if(parseInt(item.diff) > _max){
                    _max = parseInt(item.diff)
                }
                if(parseInt(item.less) > _max){
                    _max = parseInt(item.less)
                }
                if(parseInt(item.more) > _max){
                    _max = parseInt(item.more)
                }
                _indicators.push({text: 'level ' + item.category, max: _max})
            })
            _series.push({ name: 'same' , value: _sames})
            _series.push({ name: 'diff' , value: _diffs})
            _series.push({ name: 'less' , value: _lesses})
            _series.push({ name: 'more' , value: _mores})
            console.log('series_radar', _series)
            this.options = {
                tooltip: { trigger: 'axis'},
                legend: { bottom: 10,},
                symbol: 'none',
                radar: [
                    {
                        indicator: _indicators,
                        radius: 130,
                        center: ['50%', '50%']
                    }
                ],
                series: [
                    {
                        type: 'radar',
                        tooltip: {
                            trigger: 'item'
                        },
                        areaStyle: {},
                        data: _series
                    }
                ]
            }
        },
        init_data(){
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
            this.$refs["chart2"].resize()
        }
    },
}
</script>

<style lang="less" scoped>
.a{
    color: #5165a3;
}
</style>

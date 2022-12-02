<template>
    <div :ref="chart_ref" :id="chart_ref" :style="{width: '100%', height: '415px'}"></div>
</template>
<script>
let echarts = require('echarts/lib/echarts');
require('echarts/lib/chart/line');
require('echarts/lib/chart/bar');
require('echarts/lib/component/tooltip');
require('echarts/lib/component/toolbox');
require('echarts/lib/component/legend');
require('echarts/lib/component/markLine');
import { TitleComponent } from 'echarts/components';
echarts.use([TitleComponent]);
import { RadarChart } from 'echarts/charts';
echarts.use([RadarChart]);
// require('echarts/lib/component/title');
import { GridComponent } from 'echarts/components';
echarts.use([GridComponent]);
import { VisualMapComponent } from 'echarts/components';
echarts.use([VisualMapComponent]);
import { PieChart } from 'echarts/charts';
echarts.use([PieChart]);
export default {
  name: 'hello',
  props: {
    options: {
      type: Object,
      default: ()=>{}
    },
    series: {
      type: Array,
      default: ()=>[]
    },
    chart_ref:{
      type: String,
      default: 'myChart_request'
    }
  },
  data () {
    return {
      myChart: null,
    }
  },
  watch:{
    options(newval){
      var self = this
        let dom = this.$refs[self.chart_ref];
        // 销毁已创建的实例
        self.myChart = echarts.init(dom).dispose();
        // 重新创建新的实例
        self.myChart = echarts.init(dom)
        // debugger
        // 基于准备好的dom，初始化echarts实例
        // let myChart = echarts.init(document.getElementById('myChart_request'))
        // 绘制图表
        self.myChart.setOption(self.options);

    },
  },
  mounted(){
    let self = this;
    self.$nextTick(()=>{
      self.drawLine();
    })
    // window.onresize = function() {
    //   debugger
    //   self.myChart.resize()
    // }

  },
  destroyed(){
    window.onresize = null;
  },
  methods: {
    drawLine(){
        var self = this
        let dom = this.$refs[self.chart_ref];
        self.myChart = echarts.init(dom);
        // debugger
        // 基于准备好的dom，初始化echarts实例
        // let myChart = echarts.init(document.getElementById('myChart_request'))
        // 绘制图表
        self.myChart.setOption(self.options);
        setTimeout(() => {
          self.myChart.resize()  
        }, 100);
    },
    resize(){
      this.myChart.resize()
    }
  }
}
</script>

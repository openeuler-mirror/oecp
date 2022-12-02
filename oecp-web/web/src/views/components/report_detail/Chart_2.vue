<template>
    <div>
        <div class="echart_card">
            <div class="echart_title"><slot name="title"></slot></div>
            <mx-echart ref="chart2" chart_ref="myChart_2" :options="options"></mx-echart>
            <div class="action">
                <a-select v-model="rpm_type" @change="handleRpmTypeChange" style="width:200px">
                    <a-select-option value="rpm-package">rpm package change</a-select-option>
                    <a-select-option value="rpm-service">rpm service change</a-select-option>
                    <a-select-option value="rpm-config">rpm config change</a-select-option>
                    <a-select-option value="rpm-header">rpm header change</a-select-option>
                    <a-select-option value="rpm-file">rpm file change</a-select-option>
                    <a-select-option value="rpm-lib">rpm lib change</a-select-option>
                    <a-select-option value="rpm-cmd">rpm cmd change</a-select-option>
                    <a-select-option value="rpm-abi">rpm abi change</a-select-option>
                </a-select>
            </div>
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
        on_data_change(rows, x_axis_data, y_axis_title_data) {
            var _series = []
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
            })
            if(rows.length == 0){
                _series=[
                    { name: '', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: []},
                ]
            } else {
                _series = [
                    { name: y_axis_title_data[0], itemStyle:{color:'#ee6666'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_delete},
                    { name: y_axis_title_data[1], itemStyle:{color:'#3ba272'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_add},
                    { name: y_axis_title_data[2], itemStyle:{color:'#73c0de'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_release},
                    { name: y_axis_title_data[3], itemStyle:{color:'#91cc75'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_version_update},
                    { name: y_axis_title_data[4], itemStyle:{color:'#fac858'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_consistent},
                    { name: y_axis_title_data[5], itemStyle:{color:'#fc8452'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_provide_change},
                    { name: y_axis_title_data[6], itemStyle:{color:'#ea7ccc'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_require_change},
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
        on_rpm_change(rows, x_axis_data, y_axis_title_data, r_type) {
            var _series = []
            var _array_delete = []
            var _array_add = []
            var _array_consistent = []
            var _array_content_change = []
            rows.forEach(item=>{
                _array_add.push(parseInt(item.file_more))
                _array_delete.push(parseInt(item.file_less))
                _array_consistent.push(parseInt(item.file_consistent))
                _array_content_change.push(parseInt(item.file_content_change))
            })
            if(rows.length == 0){
                _series=[
                    { name: '', type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: []},
                ]
            } else {
                if(r_type == 'rpm-abi') {
                    _series = [
                        { name: '接口删除', itemStyle:{color:'#ee6666'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_delete},
                        { name: '接口变化', itemStyle:{color:'#fc8452'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_content_change},
                        { name: '新增接口', itemStyle:{color:'#3ba272'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_add},
                    ]
                } else {
                    _series = [
                        { name: y_axis_title_data[0], itemStyle:{color:'#3ba272'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_add},
                        { name: y_axis_title_data[1], itemStyle:{color:'#ee6666'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_delete},
                        { name: y_axis_title_data[2], itemStyle:{color:'#fac858'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_consistent},
                        { name: y_axis_title_data[3], itemStyle:{color:'#fc8452'}, type: 'bar', label:{ show: true, formatter: '{c}', position: 'top' }, data: _array_content_change},
                    ]
                }
            }
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
            this.init_package_data()
        },
        init_package_data(){
            var self = this
            self.loading = true
            self.$http.get(`statistical/detail/all-package/${self.r_id}`).then(res=>{
                self.loading = false
                var rows = JSON.parse(JSON.stringify(res.data.data))
                self.on_data_change(rows, ['全量软件包', 'L1软件包', 'L2软件包'], ['删除','新增','release', '版本升级', '保持一致', 'provide变化','require变化'])
            },error=>{
                self.loading = false
            })
        },
        init_rpm_data(r_type){
            var self = this
            self.loading = true
            self.$http.get(`statistical/detail/rpmfile-analyse/${self.r_id}?type=${r_type}`).then(res=>{
                self.loading = false
                var rows = JSON.parse(JSON.stringify(res.data.data))
                var prefix = ''
                switch(r_type){
                    case 'rpm-service':
                        prefix='服务';
                        break;
                    case 'rpm-config':
                        prefix='配置';
                        break;
                    case 'rpm-header':
                        prefix='头';
                        break;
                    case 'rpm-file':
                        prefix='其他';
                        break;
                    case 'rpm-lib':
                        prefix='库';
                        break;
                    case 'rpm-cmd':
                        prefix='命令';
                        break;
                    case 'rpm-abi':
                        prefix='接口';
                        break;
                }
                self.on_rpm_change(rows, ['全量软件包', 'L1软件包', 'L2软件包'], [`${prefix}文件增加`,`${prefix}文件减少`,`内容一致${prefix}文件`, `${prefix}文件内容变化`], r_type)
            },error=>{
              self.loading = false
            })
        },
        handleRpmTypeChange(r_type) {
            if(r_type == 'rpm-package'){
                this.init_package_data()
            } else {
                this.init_rpm_data(r_type)
            }
        },
        onresize(){
            this.$refs["chart2"].resize()
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
    z-index: 99;
}
</style>

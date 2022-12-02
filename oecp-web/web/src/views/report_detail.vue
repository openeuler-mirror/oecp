<template>
  <div class="my-page">
    <a-back-top />
    <mx-breadcrumb :list="route_list" />
    <div class="list_page_container">
        <div class="actions">
            <div class="detail_btn">
                <div class="btn_detail" @click="handleReportDetailClick">报告详情</div>
                <div class="btn_detail" @click="handleChangeDetailClick">变更详情</div>
            </div>
        </div>
        <div class="my_table" style="margin-top:0">
            <div class="sub_title">OSV技术测评报告</div>
            <div class="tables">
                <report-osv :report_base_id="report_base_id" style="width:1200px" />
            </div>
        </div>
        <div class="chart">
            <div class="chart_row">
                <div class="chart_item">
                    <div class="chart_title">
                        <img class="icon" src="@/assets/img/divider.png"  alt='' />
                        rpm package change</div>
                    <chart_pie :r_id="report_base_id" ref="chart1" />
                </div>
                <div class="chart_item">
                    <div style="text-align:right">
                        <div class="chart_title">
                            <img class="icon" src="@/assets/img/divider.png"  alt='' />
                            rpm file analyse</div>
                        <chart2 :r_id="report_base_id" ref="chart2" />
                    </div>
                </div>
            </div>
        </div>
        <div class="my_table">
            <div class="sub_title">rpm package Analyse</div>
            <div class="tables">
                <change-package :report_base_id="report_base_id" style="width:800px" />
            </div>
        </div>
        <div class="my_table">
            <div class="sub_title">rpmfile Analyse</div>
            <div class="tables">
                <change-rpm :report_base_id="report_base_id" />
            </div>
        </div>
        <div class="my_table">
            <div class="sub_title">rpmabi Analyse</div>
            <div class="tables">
                <rpm-abi :report_base_id="report_base_id"  style="width:600px"/>
            </div>
        </div>
        <div class="my_table">
            <div class="sub_title">Kernel Analyse</div>
            <div class="tables">
                <change-kabi :report_base_id="report_base_id" style="width:600px" />
            </div>
        </div>
    </div>
  </div>
</template>

<script>
import 'ant-design-vue'
import MxBreadcrumb from '@/components/mx-breadcrumb/index.vue'
import chart1 from './components/report_detail/Chart_1.vue'
import chart2 from './components/report_detail/Chart_2.vue'
import chart3 from './components/report_detail/Chart_3.vue'
import chart_pie from './components/report_detail/Chart_pie.vue'
import chart4 from './components/report_detail/Chart_4.vue'
import AllReportResult from './components/report_detail/all_report_result.vue'
import ChangePackage from './components/report_detail/change_package.vue'
import ChangeRpm from './components/report_detail/change_rpm.vue'
import ChangeKabi from './components/report_detail/change_kabi.vue'
import ReportOsv from './components/report_detail/report_osv.vue'
import RpmItem from './components/report_detail/rpm_item.vue'
import RpmAbi from './components/report_detail/rpm_abi.vue'
import SimilarCalculateResult from './components/report_detail/similar_calculate_result.vue'

export default {
    name: 'page',
    components: {
        MxBreadcrumb,
        chart1,
        chart2,
        chart3,
        chart4,
        chart_pie,
        AllReportResult,
        ChangePackage,
        ChangeRpm,
        ChangeKabi,
        ReportOsv,
        SimilarCalculateResult,
        RpmItem,
        RpmAbi
    },
    data () {
        return {
            loading: false,
            report_title: '2202.03.ISO VS SP3.ISO',
            info: {},
            report_base_id: '',
            route_list: [
                {icon: 'home', title: '首页', route_path: 'index'},
                {icon: 'appstore', title: '报告展示', route_path: 'home'},
                {icon: 'file', title: '报告总览'},
            ],
        }
    },
    computed: {
    },
    mounted() {
        var self = this
        self.report_base_id = this.$route.query.report_base_id
        self.getData()
        window.onresize = () => {
            this.$refs["chart1"].onresize()
            this.$refs["chart2"].onresize()
            // this.$refs["chart3"].onresize()
            // this.$refs["chart4"].onresize()
        }
        this.$nextTick(()=>{
            self.$refs.chart1.init_data()
            self.$refs.chart2.init_data()
            // self.$refs.chart3.init_data()
            // self.$refs.chart4.init_data()
        })
    },
    methods: {
        /**
         * 报告详情
         */
        handleReportDetailClick(){
            this.$router.push({name: 'all_rpm_report', query:{
                r_bid: this.report_base_id
            }})
        },
        /**
         * 变更详情
         */
        handleChangeDetailClick(){
            this.$router.push({name: 'difference_detail', query:{
                report_base_id: this.report_base_id
            }})
        },
        getData () {
            var self = this
            self.loading = true
            self.$http.get(`report/compare/iso-info/${self.report_base_id}`).then(res=>{
                self.loading = false
                this.info = JSON.parse(JSON.stringify(res.data.data))
            },error=>{
              self.loading = false
            })
        },
    }
}
</script>

<style lang="less" scoped>
.title{
    font-size: 30px;
    font-family: Source Han Sans CN-Regular, Source Han Sans CN;
    font-weight: 400;
    color: #333333;
    .vs{
        color: red;
    }
}
.actions{
    position: absolute;
    top: 0;
    right: 0;
    // width: 100%;
    display: flex;
    justify-content: space-around;
    padding: 20px 0;
    padding-right: 20px;
    .detail_btn{
        // margin-top: 40px;
        width: 140px;
        display: flex;
        justify-content: space-between;
        .btn_detail{
            // width:150px;
            // height: 50px;
            font-size: 16px;
            padding: 0;
            color: #3e8bfe;
            cursor: pointer;
            text-decoration: underline;
        }
    }
}
.my_table{
    margin-top: 40px;
    .sub_title{
        padding-bottom: 25px;
        font-size: 26px;
        text-decoration: underline;
        font-family: Source Han Sans CN-Regular, Source Han Sans CN;
        font-weight: 400;
        color: #333333;
    }
}
.chart_title{
    background: #F3F7FE;
    border-radius: 2px;
    height: 40px;
    padding: 0 20px;
    display: flex;
    align-items: center;
    box-sizing: border-box;
    font-size: 14px;
    font-family: Source Han Sans CN-Regular, Source Han Sans CN;
    font-weight: bold;
    color: #333333;
    margin: 40px 20px 0 20px;
    img{
        margin-right: 10px;
    }
}
.chart_row{
    display: flex;
    width: 100%;
    .chart_item{
        flex: 1;
        background: #fff;
        margin: 20px;
        position: relative;
        padding-bottom: 20px;
    }
}
</style>

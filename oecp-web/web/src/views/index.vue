<template>
  <div class="my-page">
    <div class="left">
        <div class="header">
            <div class="title_en">OECP Report</div>
            <div class="title">OECP报告展示</div>
            <div class="title_content">openEuler各版本间差异化报告分析、镜像差异分析等报告展示项目</div>
        </div>
        <div class="actions">
            <div class="btn" @click="handleBuildClick">差异分析</div>
            <div class="btn" @click="handleReportClick">报告查询</div>
        </div>
    </div>
    <div class="right">
        <img src="@/assets/img/report_img.png" />
    </div>
  </div>
</template>

<script>
import 'ant-design-vue'
export default {
    name: 'tables_page',
    data () {
        return {
        }
    },
    computed: {
    },
    mounted() {
    },
    methods: {
        handleBuildClick(){
            this.$router.push('upload?tab=taggz')
        },
        handleReportClick(){
            this.$router.push('home')
        },
    }
}
</script>

<style lang="less" scoped>
    .my-page{
        width: 980px;
        margin: 0 auto;
        display: flex;
        padding-top: 200px;
        .left{
            flex: 1;
            .header{
                .title_en{
                    height: 50px;
                    line-height: 70px;
                    font-size: 32px;
                    font-weight: bold;
                    // font-family: Avenir,Helvetica,Arial,sans-serif;
                    font-family: Arial, Helvetica, sans-serif;
                    
                    // font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
                    // arial
                }
                .title{
                    height: 100px;
                    display: flex;
                    align-items: center;
                    font-size: 53px;
                    color: #333333;
                }
                .title_content{
                    position: relative;
                    // top: 0px;
                    font-size: 16px;
                    font-family: Avenir,Helvetica,Arial,sans-serif;
                    color: #242424;
                }
            }
            .actions{
                width: 400px;
                margin-top: 50px;
                display: flex;
                justify-content: space-between;
                .btn{
                    width: 180px;
                    height: 60px;
                    display: flex;
                    justify-content: space-around;
                    align-items: center;
                    background: rgb(24, 144, 255);
                    color: #fff;
                    box-shadow: 10px 10px 6px rgba(24, 144, 255, 0.2);
                    border-radius: 2px;
                    cursor: pointer;
                    font-size: 18px;
                }
            }
        }
        .right{
            flex: 1;
            img{

                width: 100%;
                border-radius: 2px;
                    box-shadow: 10px 10px 6px rgba(24, 144, 255, 0.2);
            }

        }
    }
</style>

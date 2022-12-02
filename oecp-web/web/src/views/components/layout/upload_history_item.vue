<template>
    <div>
        <div class="history" style="width: 320px;height: 310px;">
            <a-carousel :dots="false" ref="carousel_upload">
                <div style="height:260px" v-for="(item_data, index) in his_data" :key="index">
                    <div v-if="item_data.date" class="his_title">
                        <div class="date">{{item_data.date}}</div>
                        <div class="result error" v-if="item_data.status=='ERROR'">失败</div>
                        <div class="result success" v-else>成功</div>
                    </div>
                    <a-steps progress-dot direction="vertical" size="small" :current="item_data.step" :status="(item_data.status=='ERROR' ?'error':'finish')">
                        <a-step title="选择报告" disabled>
                            <div slot="description">选择要上传的tar.giz压缩报告</div>
                        </a-step>
                        <a-step title="上传报告" disabled>
                            <template v-if="item_data.step == 1 && item_data.status=='ERROR'">
                                <div slot="description">{{item_data.error_msg}}</div>
                            </template>
                            <template v-else>
                                <div slot="description">上传报告至服务器</div>
                            </template>
                        </a-step>
                        <a-step title="解析报告" disabled>
                            <template v-if="item_data.step == 2 && item_data.status=='ERROR'">
                                <div slot="description">{{item_data.error_msg}}</div>
                            </template>
                            <template v-else>
                                <div slot="description">解析上传的报告,并持久化</div>
                            </template>
                        </a-step>
                        <a-step title="完成" disabled description="完成报告上传、解析、持久化"/>
                    </a-steps>
                </div>
            </a-carousel>
            <div style="text-align:center;">
                <a-pagination :pageSize="1" show-less-items :default-current="1" :total="his_data.length" @change="page_change" />
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'tables_page',
    props:{
        his_data: {
            type: Array,
            default: () => {}
        }
    },
    data () {
        return {
        }
    },
    mounted() {
    },
    
    methods: {
        page_change(page){
            this.$refs.carousel_upload.goTo(page, false)
        }
    }
}
</script>

<style lang="less" scoped>
.his_title{
    display: flex;
    justify-content: space-between;
    align-items: center;
    .date{
        font-size: 14px ;
        padding: 10px 0;
        font-weight: bold;
    }
    .result{
        font-weight: bold;
        &.success{
            color: #52c41a;
        }
        &.error{
            color: #f5222d;
        }
    }
}
/deep/ .ant-steps-item-content{
    width: 270px!important;
}
</style>

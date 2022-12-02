<template>
    <a-config-provider :locale="locale">
        <a-layout id="components-layout-demo-custom-trigger">
            <a-layout-header class="mx_header">
                <div class="mx_title">OECP报告展示</div>
                <div class="mx_actions">
                </div>
            </a-layout-header>
            <a-layout>
                <a-layout-content>
                    <router-view ref="tabContent"></router-view>
                    <div style="height: 30px"></div>
                </a-layout-content>
            </a-layout>
        </a-layout>
    </a-config-provider>
</template>

<script>
import zh_CN from "ant-design-vue/es/locale/zh_CN";
import uploadHistoryItem from "./components/layout/upload_history_item.vue";
import buildHistoryItem from "./components/layout/build_history_item.vue";
export default {
    name: "Home",
    components:{
        uploadHistoryItem,
        buildHistoryItem
    },
    data() {
        return {
            locale: zh_CN,
            upload_history: [],
            build_history: [],
        }
    },
    watch: {
        '$route': function (newRoute) {
            if(newRoute.name != 'name') {
                this.init_upload();
                this.init_build();
            }
        }
    },
    created() {
        this.upload_history = JSON.parse(localStorage.getItem('upload_history'))
        this.build_history = JSON.parse(localStorage.getItem('build_history'))
    },

    methods: {
        handleUploadReport() {
            if(this.$route.name != 'upload') {
                this.$router.push({path:'/upload', query:{
                    tab: 'taggz'
                }})
            } else {
                if(!this.$route.query || !this.$route.query.tab || this.$route.query.tab != 'taggz'){
                    this.$router.replace({
                        path:'/upload',
                        query: {
                            tab: 'taggz'
                        }
                    })
                }
            }
        },
        handleBuildReport() {
            if(this.$route.name != 'upload') {
                this.$router.push({path:'/upload', query:{
                    tab: 'iso'
                }})
            } else {
                if(!this.$route.query || !this.$route.query.tab || this.$route.query.tab != 'iso'){
                    this.$router.replace({
                        path:'/upload',
                        query: {
                            tab: 'iso'
                        }
                    })
                }
            }
        },
        init_upload() {

        },
        init_build(){

        },
        /** 清空上传记录 */
        handleClearUploadHistory(){
            var self = this
            this.$confirm({
                title: "清空记录",
                content: "您确定要清空上传记录吗?",
                okText: "确定",
                cancelText: "取消",
                onOk: () => {
                    localStorage.removeItem('upload_history')
                    self.upload_history = []
                }
            });
        },
        /** 清空生成记录 */
        handleClearBuildHistory(){
            var self = this
            this.$confirm({
                title: "清空记录",
                content: "您确定要清空生成记录吗?",
                okText: "确定",
                cancelText: "取消",
                onOk: () => {
                    localStorage.removeItem('build_history')
                    self.build_history = []
                }
            });
        }
    },
    computed: {},
};
</script>

<style lang="less" scoped>
.mx_header {
  display: flex;
  z-index: 9;
  height: 72px;
  background: #fff;
  box-shadow: 1px 1px 5px 1px rgb(194, 213, 243, 0.51);
//   padding: 0 48px 0 30px;
    padding-left: 50px;
    padding-right: 0;
}

.logo {
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  margin: 16px;
  color: #fff;
  text-align: center;
  line-height: 32px;
}
.mx_logo {
  padding: 0 20px;
  // display: inline-block;
  height: 72px;
  line-height: 720px;
  font-size: 0;
}
.mx_logo img {
  display: inline-block;
  vertical-align: middle;
  width: 42px;
  height: 33px;
}
.mx_title {
  display: inline-block;
  font-size: 23px;
  font-family: AlibabaPuHuiTi;
  font-weight: 400;
  color: #1890ff;
  height: 72px;
  line-height: 72px;
  flex: 1;
}
.mx_actions {
  text-align: right;
  display: flex;
  align-items: center;
  .item {
    flex: 1;
    height: 40px;
    line-height: 40px;
    padding: 0 20px;
    font-size: 16px;
    color: #1890ff;
    cursor: pointer;
    &:last-child {
        margin-right: 100px;
    }
  }
}
.breadcrumb_item:hover{
    color: #1890ff;
    cursor: pointer;
}
/deep/ .ant-carousel .slick-dots li.slick-active button{
    background: #333333;
}
/deep/ .ant-carousel .slick-dots li button{
    background: #333333;
}
.his_head{
    display: flex;
    height: 40px;
    align-items: center;
    .his_title{
        flex: 1;
    }
    .his_cache_clear{
        color: #1890ff;
        cursor: pointer;
    }
}
</style>

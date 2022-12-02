<template>
    <div class="my-page">
        <mx-breadcrumb :list="route_list" />
        <div class="tabview">
            <a-radio-group v-model="tab" button-style="solid" @change="tab_change">
                <a-radio-button value="taggz">
                差异报告分析
                </a-radio-button>
                <a-radio-button value="iso">
                镜像差异分析
                </a-radio-button>
            </a-radio-group>
        </div>
        <div v-if="tab=='taggz'">
            <mx-upload ref="upload_com" />
        </div>
        <div v-if="tab=='iso'">
            <mx-build ref="build_com" />
        </div>
    </div>
</template>
<script>
import MxBreadcrumb from '@/components/mx-breadcrumb/index.vue'
import MxUpload from './components/upload/upload.vue'
import MxBuild from './components/upload/build.vue'
export default {
    components:{
        MxBreadcrumb,
        MxUpload,
        MxBuild
    },
    data() {
        return {
            tab: 'taggz', // taggz:差异报告分析，iso:生成报告
            route_list: [
                {icon: 'home', title: '首页', route_path: 'index'},
                {icon: 'cloud-upload', title: '差异报告分析'},
            ],
        };
    },
    watch:{
        tab(val){
            if(val == 'taggz'){
                this.route_list = [
                    {icon: 'home', title: '首页', route_path: 'index'},
                    {icon: 'cloud-upload', title: '差异报告分析'},
                ]
            }
            if(val == 'iso'){
                this.route_list = [
                    {icon: 'home', title: '首页', route_path: 'index'},
                    {icon: 'build', title: '镜像差异分析'},
                ]
            }
        },
        '$route': function (newRoute) {
            if(newRoute.query.tab) {
                this.tab = newRoute.query.tab
                this.$nextTick(()=>{
                    if(this.tab == 'taggz'){
                        this.init_upload()
                    } else {
                        this.init_build()
                    }
                })
            }
        }
    },
    mounted() {
        this.tab = this.$route.query.tab
        this.$nextTick(()=>{
            if(this.tab == 'taggz'){
                this.init_upload()
            } else {
                this.init_build()
            }
        })
    },
    methods: {
        tab_change(e) {
            console.log(e.target.value)
            if(e.target.value == 'iso'){
                this.init_build()
            } else{
                this.init_upload()
            }
        },
        init_upload() {
            if(localStorage.getItem('upload_progress')){
                let upload_progress = JSON.parse(localStorage.getItem('upload_progress'))
                console.log('upload_progress', upload_progress)
                this.$nextTick(()=>{
                    this.$refs.upload_com.init_cache(upload_progress)
                })
            }
        },
        init_build(){
            if(localStorage.getItem('buid_progress')){
                let buid_progress = JSON.parse(localStorage.getItem('buid_progress'))
                console.log('buid_progress', buid_progress)
                this.$nextTick(()=>{
                    this.$refs.build_com.init_cache(buid_progress)
                })
            }
        }
    },
    beforeRouteLeave(to, from, next){
        if(this.$refs.upload_com){
            this.$refs.upload_com.clear_ticker()
        }
        if(this.$refs.build_com){
            this.$refs.build_com.clear_ticker()
        }
        next()
    }
};
</script>
<style scoped lang="less">
.my-page{
    margin: 0;
    padding: 25px 16px 24px 16px;
    // background: #fff;
}
.tabview{
    width: 100%;
    text-align: center;
}
</style>
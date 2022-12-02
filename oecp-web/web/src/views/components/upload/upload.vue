<template>
    <div class="mxview">
        <div class="mxsteps">
            <a-steps :current="step" labelPlacement="vertical">
                <a-step title="选择报告">
                    <div slot="description">选择要上传的tar.giz压缩报告</div>
                </a-step>
                <a-step title="上传报告">
                    <div slot="description">上传报告至服务器</div>
                </a-step>
                <a-step title="解析报告">
                    <!-- <template v-if="step=2">
                        <a-icon slot="icon" type="loading" />
                    </template> -->
                    <div slot="description">解析上传的报告,并持久化</div>
                </a-step>
                <a-step title="完成" description="完成报告上传、解析、持久化"/>
            </a-steps>
        </div>
        <div class="uploadview">
            <template v-if="status=='PENDING'">
                <div v-show="step==0">
                    <a-upload-dragger :customRequest="upload" name="file" :multiple="false">
                        <div style="padding:50px 0">
                            <p class="ant-upload-drag-icon">
                                <a-icon type="cloud-upload" :style="{color:'#0F3B93'}"  />
                            </p>
                            <p class="ant-upload-text">将文件拖拽到此处，或点击上传</p>
                        </div>
                    </a-upload-dragger>
                </div>
                <div v-if="step==1">
                    <div class="flieview">
                        <div class="item">
                            <div class="chooseview">
                                <a-progress type="circle" :width="150" :strokeWidth="10" :percent="files[0].progress" trailColor="rgb(15, 59, 147, 0.1)" />
                            </div>
                            <div class="title" v-show="files[0].filename">
                                <a-space>
                                    <div class="icon">
                                        <a-icon type="file-zip" />
                                    </div>
                                    <div>{{files[0].filename}}</div>
                                </a-space>
                            </div>
                        </div>
                    </div>
                </div>
                <div v-if="step==2">
                    <div class="tipview">
                        <div v-if="files[0].db_total == 0">
                            <a-space>
                                <a-icon slot="icon" type="loading" /><span>上传成功，正在解析报告……</span>
                            </a-space>
                        </div>
                        <div  v-if="files[0].db_total > 0">
                            <a-space>
                                <a-icon slot="icon" type="loading" /><span>({{files[0].db_finish}}/{{files[0].db_total}}) 解析完成，正在导入数据库……</span>
                            </a-space>
                        </div>
                    </div>
                </div>
                <div v-if="step==3">
                    <a-result status="success" :title="files[0].filename + '报告已全部导入成功'">
                        <template #extra>
                            <a-button key="console" @click="handleGoHome">
                                返回首页
                            </a-button>
                            <a-button key="buy" type="primary" @click="handleReUpload">
                                重新导入
                            </a-button>
                        </template>
                    </a-result>
                </div>
            </template>
            <template v-if="status == 'ERROR'">
                <a-result status="error" :title="error_msg">
                    <template #extra>
                        <a-button key="console" @click="handleGoHome">
                            返回首页
                        </a-button>
                        <a-button key="buy" type="primary" @click="handleReUpload">
                            重新导入
                        </a-button>
                    </template>
                </a-result>
            </template>
            <template v-if="status=='SUCCESS'">
                <div v-if="step==3">
                    <a-result status="success" :title="files[0].filename + '报告已全部导入成功'">
                        <template #extra>
                            <a-button key="console" @click="handleGoHome">
                                返回首页
                            </a-button>
                            <a-button key="buy" type="primary" @click="handleReUpload">
                                重新上传
                            </a-button>
                        </template>
                    </a-result>
                </div>
            </template>
        </div>
    </div>
</template>
<script>

import {dateFormat} from '@/libs/util';
export default {
    filters: {
        btnTextFilter(val) {
            return val ? '暂停' : '继续'
        }
    },
    data() {
        return {
            step: 0,
            // action_id: '',
            files: [
                {progress: 0, filename: '', file: {}, db_finish: 0, db_total: 0}
            ],
            status: 'PENDING', // ERROR,PENDING,SUCCESS
            error_msg: '', // 错误信息
            task_id: 0,
            ticker: null,
            ticker_time: 3000, // 定时器间隔时间
        }
    },
    methods: {
        /**
         * 从缓存加载
         */
        init_cache(cache) {
            var self = this
            self.step = cache.step
            // self.action_id= cache.action_id
            self.files = cache.files
            self.status = cache.status
            self.error_msg = cache.error_msg
            self.task_id = cache.task_id
            self.get_progress_by_task_id()
        },
        /**
         * 返回首页
         */
        handleGoHome(){
            this.$router.push('/')
        },
        /**
         * 重新导入
         */
        handleReUpload(){
            this.step = 0,
            this.files = [
                {progress: 0, filename: '', file: {}, db_finish: 0, db_total: 0}
            ],
            this.status = 'PENDING', // ERROR,PENDING,SUCCESS
            this.error_msg= '', // 错误信息
            this.task_id = 0,
            this.ticker = null
        },
        upload(_file) {
            // debugger
            var self = this
            var file = _file.file
            self.files = [{progress: 0, filename: file.name, file: file, db_finish: 0, db_total: 0}]
            // self.action_id = _file.name // uuid.v4().substring(0,8)
            self.step = 1
            var formData = new FormData();
            formData.append('title', file.name);
            formData.append('file', file);
            return self.$http.upload('upload/tar-gz', formData,
            (progressEvent) => {
                // debugger
                let completeVal = (progressEvent.loaded * 1000 / progressEvent.total)  || 10;
                let _ptogress = parseFloat((parseInt(completeVal) / 10).toFixed(1))
                self.files[0].progress = _ptogress
            }).then(res => {
                if (res.data.code === '200') { // 成功
                    self.task_id = res.data.data
                    self.step = 2
                    self.get_progress_by_task_id()
                    self.set_upload_progress_cache()
                } else {
                    self.status = 'ERROR'
                    self.error_msg = res.data.message
                }
            })
        },
        /**
         * 根据任务id查询任务进度
         */
        async get_progress_by_task_id(){
            var self = this
            self.ticker = setInterval(async () => {
                var res = await self.$http.get(`upload/async/state/${self.task_id}`)
                if(res.data.code == '200'){
                    if(res.data.data.status == 'SUCCESS'){ // 解析完成
                        self.step = 3
                        self.status = 'SUCCESS'
                        clearInterval(self.ticker)
                        self.clear_upload_progress_cache()
                    } else if(res.data.data.status == 'PROGRESS'){
                        // 解析中
                        var result = res.data.data.result
                        self.step = 2
                        // debugger
                        self.files[0].db_total = result.total
                        self.files[0].db_finish = result.finish
                        // if(result.total > 0) // 解析完成，正在做数据持久化
                        self.set_upload_progress_cache()
                    } else if(res.data.data.status == 'FAILED'){ // 导入失败
                        self.step = 2
                        self.status = 'ERROR'
                        self.error_msg = res.data.data.result.message
                        clearInterval(self.ticker)
                        self.clear_upload_progress_cache()
                    }
                } else {
                    console.log('查询任务进度异常')
                    self.status = 'ERROR'
                    self.error_msg = res.data.message
                    clearInterval(self.ticker)
                    self.clear_upload_progress_cache()
                }
            }, self.ticker_time);
        },
        
        /**
         * 设置生成进度缓存
         */
        set_upload_progress_cache(){
            var _cache = JSON.stringify({
                step: this.step,
                files: this.files,
                task_id: this.task_id,

                // action_id: this.action_id,
                status: this.status,
                error_msg: this.error_msg // 错误信息
            })
            localStorage.setItem('upload_progress', _cache)
        },
        /**
         * 清除缓存并将结果记录在操作记录缓存中
         */
        clear_upload_progress_cache(){
            localStorage.removeItem('upload_progress')
            var _cache = {
                step: this.step,
                files: this.files,
                task_id: this.task_id,
                // action_id: this.action_id,
                status: this.status,
                error_msg: this.error_msg, // 错误信息
                date: dateFormat(new Date(), 'yyyy-MM-dd HH:mm:ss')
            }
            if(localStorage.getItem('upload_history')){
                var history = JSON.parse(localStorage.getItem('upload_history'))
                history.unshift(_cache)
                localStorage.setItem('upload_history', JSON.stringify(history))
            } else {
                var history = [_cache]
                localStorage.setItem('upload_history', JSON.stringify(history))
            }
        },
        clear_ticker(){
            clearInterval(this.ticker)
        }
    },
};
</script>
<style scoped lang="less">
.mxview{
    width: 100%;
    margin: 30px 0;
    .mxsteps{
        width: 800px;
        margin: 0 auto;
    }
    .uploadview{
        margin: 20px 0;
    }
}
.tabview {
  width: 100%;
  text-align: center;
}

.chooseview{

    display: flex;
    flex-flow: row;
    justify-content: space-around;
    vertical-align: middle;
}
.tipview{
    width: 100%;
    padding: 50px 0;
    // height: 150px;
    align-items: center;
    text-align: center;
    display: flex;
    flex-flow: row;
    justify-content: space-around;
    vertical-align: middle;
    line-height: 40px;
    font-size: 20px;
}
</style>
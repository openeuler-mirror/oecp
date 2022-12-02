<template>
    <div class="mxview">
        <div class="mxsteps">
            <a-steps :current="step" labelPlacement="vertical">
                <a-step title="选择报告">
                    <div slot="description">选择要上传的iso镜像</div>
                </a-step>
                <a-step title="上传镜像文件">
                    <div slot="description">上传镜像文件至服务器</div>
                </a-step>
                <a-step title="oecp工具分析">
                    <div slot="description">解析iso，并生成报告</div>
                </a-step>
                <a-step title="解析报告">
                    <div slot="description">解析生成的报告,并持久化</div>
                </a-step>
                <a-step title="完成" description="完成iso上传、解析、持久化"/>
            </a-steps>
        </div>
        
        <template v-if="status=='PENDING'">
            <div class="uploadview" v-show="step==0">
                <div class="flieview">
                    <div class="item">
                        <div class="title">
                            <a-space>
                                <div>基线镜像文件</div>
                            </a-space>
                        </div>
                        <div class="chooseview">
                            <template v-if="files[0].progress==100">
                                <a-progress type="circle" :width="150" :strokeWidth="10" :percent="files[0].progress" trailColor="rgb(15, 59, 147, 0.1)" />
                            </template>
                            <template v-else>
                                <mx-dragger>
                                    <div class="dragger" @click="handleChooseFileClick(0)">
                                        <div v-if="files[0] && files[0].filename">
                                            <p class="ant-upload-drag-icon">
                                                <a-icon type="file-zip" :style="{color:'#0F3B93',fontSize:'50px'}"  />
                                            </p>
                                        </div>
                                        <div v-else>
                                            <p class="ant-upload-drag-icon">
                                                <a-icon type="cloud-upload" :style="{color:'#0F3B93',fontSize:'50px'}"  />
                                            </p>
                                            <p class="ant-upload-text">将文件拖拽到此处，或点击上传</p>
                                        </div>
                                    </div>
                                </mx-dragger>
                            </template>
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
                    <div class="item">
                        <div class="title">
                            <a-space>
                                <div>待测评镜像文件</div>
                            </a-space>
                        </div>
                        <div class="chooseview">
                            <template v-if="files[1].progress==100">
                                <a-progress type="circle" :width="150" :strokeWidth="10" :percent="files[1].progress" trailColor="rgb(15, 59, 147, 0.1)" />
                            </template>
                            <template v-else>
                                <mx-dragger>
                                    <div class="dragger" @click="handleChooseFileClick(1)">
                                        <div v-if="files[1] && files[1].filename">
                                            <p class="ant-upload-drag-icon">
                                                <a-icon type="file-zip" :style="{color:'#0F3B93',fontSize:'50px'}"  />
                                            </p>
                                        </div>
                                        <div v-else>
                                            <p class="ant-upload-drag-icon">
                                                <a-icon type="cloud-upload" :style="{color:'#0F3B93',fontSize:'50px'}"  />
                                            </p>
                                            <p class="ant-upload-text">将文件拖拽到此处，或点击上传</p>
                                        </div>
                                    </div>
                                </mx-dragger>
                            </template>
                        </div>
                        <div class="title" v-show="files[1].filename">
                            <a-space>
                                <div class="icon">
                                    <a-icon type="file-zip" />
                                </div>
                                <div>{{files[1].filename}}</div>
                            </a-space>
                        </div>
                    </div>
                </div>
                <div class="actionview">
                    <a-button type="primary" size="large" style="margin-top: 16px" @click="handleBeginUpload">
                        <template v-if="files[0].progress==100 && files[1].progress==100">
                            开始生成
                        </template>
                        <template v-else>
                            开始上传
                        </template>
                    </a-button>
                </div>
            </div>
            <div class="uploadview" v-show="step==1">
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
                    <div class="item">
                        <div class="chooseview">
                            <a-progress type="circle" :width="150" :strokeWidth="10" :percent="files[1].progress" trailColor="rgb(15, 59, 147, 0.1)" />
                        </div>
                        <div class="title" v-show="files[1].filename">
                            <a-space>
                                <div class="icon">
                                    <a-icon type="file-zip" />
                                </div>
                                <div>{{files[1].filename}}</div>
                            </a-space>
                        </div>
                    </div>
                </div>
            </div>
            <div v-if="step==2">
                <div class="tipview">
                    <div>
                        <a-space>
                            <a-icon slot="icon" type="loading" /><span>上传成功，正在解析iso文件……</span>
                        </a-space>
                    </div>
                </div>
            </div>
            <div v-if="step==3">
                <div class="tipview">
                    <div v-if="files[0].db_total == 0">
                        <a-space>
                            <a-icon slot="icon" type="loading" /><span>正在生成报告……</span>
                        </a-space>
                    </div>
                    <div  v-if="files[0].db_total > 0">
                        <a-space>
                            <a-icon slot="icon" type="loading" /><span>({{files[0].db_finish}}/{{files[0].db_total}}) 解析完成，正在导入数据库……</span>
                        </a-space>
                    </div>
                </div>
            </div>
        </template>
        <template v-if="status=='SUCCESS'">
            <div v-if="step==4">
                <a-result status="success" :title="files[0].filename + '报告已全部生成并导入成功'">
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
        <template v-if="status == 'ERROR'">
            <a-result status="error" :title="error_msg">
                <template #extra>
                    <a-button key="console" @click="handleGoHome">
                        返回首页
                    </a-button>
                    <a-button key="buy" type="primary" @click="handleReUpload">
                        重新上传
                    </a-button>
                </template>
            </a-result>
        </template>
        <input type="file" @change="handleChangeFileComplate" class="input_file" ref="file_upload0" />
        <input type="file" @change="handleChangeFileComplate" class="input_file" ref="file_upload1" />
        <ChooseFileForm :FileItemIndex="fileItemIndex" :isShowForm="isShowChooseFileForm" @cancel="handleCloseChooseFileForm" @confirmChooseFileFromLocal="confirmChooseFileFromLocal" @confirmChooseFileFromServer="confirmChooseFileFromServer" />
    </div>
</template>
<script>
import {dateFormat} from '@/libs/util';
import MxDragger from '@/components/mx-dragger/index.vue'
import ChooseFileForm from './components/chooseFileForm.vue'
import {fileToBase64} from '@/libs/util';
// const uuid = require('uuid')
export default {
    components:{
        MxDragger,
        ChooseFileForm
    },
    data() {
        return {
            // action_id: '',
            step: 0,
            files: [
                {progress: 0, filename: '', file: {}, size: 0, total_num: 0, chunk_num: 0, chunk_files: [], merge_task_id: 0, merge_status: 'PROGRESS'},
                {progress: 0, filename: '', file: {}, size: 0, total_num: 0, chunk_num: 0, chunk_files: [], merge_task_id: 0, merge_status: 'PROGRESS'}
            ],
            oecp_task_id: 0, // 分析任务进度
            status: 'PENDING', // ERROR,PENDING,SUCCESS
            error_msg: '', // 错误信息
            ticker: null,
            
            fileItemIndex: 0, // 文件序号0：第一个ISO文件，1：第二个ISO文件
            slice_size: 1024 * 1024 * 5,

            isShowChooseFileForm: false,
            uploader: null,
            uploading: false,
            ticker_time: 3000, // 定时器间隔时间
        };
    },
    methods: {
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
                {progress: 0, filename: '', file: {}, size: 0, total_num: 0, chunk_num: 0, chunk_files: [], merge_task_id: 0, merge_status: 'PROGRESS'},
                {progress: 0, filename: '', file: {}, size: 0, total_num: 0, chunk_num: 0, chunk_files: [], merge_task_id: 0, merge_status: 'PROGRESS'}
            ],
            this.status = 'PENDING', // ERROR,PENDING,SUCCESS
            this.error_msg= '', // 错误信息
            this.oecp_task_id = 0,
            this.ticker = null
        },
        /**
         * 打开上传选择框
         */
        handleChooseFileClick(fileItemIndex){
            this.fileItemIndex = fileItemIndex
            this.isShowChooseFileForm = true
        },
        /**
         * 关闭上传选择框
         */
        handleCloseChooseFileForm(){
            this.isShowChooseFileForm = false
        },
        /**
         * 确认从本地上传文件
         */
        confirmChooseFileFromLocal(res){
            // let file_item_index = res.file_item_index
            this.isShowChooseFileForm = false
            this.$refs['file_upload' + res.file_item_index].click()
            console.log('file_item_index', res.file_item_index)
        },
        /**
         * 确认从服务器选择文件
         */
        confirmChooseFileFromServer(res) {
            var self = this
            if(self.files[1 - res.file_item_index] && res.file_name == self.files[1 - res.file_item_index].filename) {
                self.$message.error('请选择不同的ISO文件');
                return
            }
            this.isShowChooseFileForm = false
            self.files[res.file_item_index].merge_status = 'SUCCESS'
            self.files[res.file_item_index].progress = 100
            self.files[res.file_item_index].filename = res.file_name
        },
        
        /**
         * 确认选择本地文件
         */
        async handleChangeFileComplate(e){
            var self = this
            let files = e.srcElement.files;
            if (files && files.length > 0) {
                let file = files[0]
                if(self.files[1 - self.fileItemIndex] && file.name == self.files[1 - self.fileItemIndex].filename) {
                    self.$message.error('请选择不同的ISO文件');
                    return
                }
                // todo: 判断系统中是否已经上传过该文件
                self.files[self.fileItemIndex].file = file
                self.files[self.fileItemIndex].filename = file.name
                self.files[self.fileItemIndex].size = file.size
                self.files[self.fileItemIndex].identifier = file.name // uuid.v4().substring(0,8)
                // 计算共需要切多少片
                let total_num = Math.ceil(file.size/ self.slice_size);
                self.files[self.fileItemIndex].total_num = total_num
                self.files[self.fileItemIndex].chunk_num = 0 // 当前需要上传第几个切片（如果是重新进入页面，则在缓存里取上传记录）
                // var _file_chun_cache = localStorage.getItem(file.name)
                // if(_file_chun_cache) {
                //     self.files[self.fileItemIndex].chunk_num = parseInt(_file_chun_cache)
                // }
                self.$http.get('upload/exists/upload-file', {filename: file.name}).then(res=>{
                    var file_exits = res.data.data
                    if(file_exits) { // 存在同名文件
                        self.files[self.fileItemIndex].merge_status='SUCCESS'
                        self.files[self.fileItemIndex].progress=100
                    } else {
                        // 不存在同名文件，则判断缓存中是否有未上传完成的文件切片
                        var _file_chun_cache = localStorage.getItem(file.name)
                        if(_file_chun_cache) {
                            self.files[self.fileItemIndex].chunk_num = parseInt(_file_chun_cache)
                        }
                    }
                })
            }
        },
        /**
         * 点击开始上传按钮
         */
        async handleBeginUpload() {
            var self = this
            self.step = 1
            // debugger
            if(self.files[0].file && self.files[1].file) {
                self.step = 1
                if(self.files[0].merge_status == 'SUCCESS' && self.files[1].merge_status == 'SUCCESS'){
                    // 服务器上两个文件都存在，直接开始比对
                    self.step = 2
                    self.build_oecp_report()
                } else {
                    for(var i = 0; i < 2; i++) {
                        let _file_item_index = JSON.parse(JSON.stringify(i))
                        let _file_chun_index = self.files[_file_item_index].chunk_num + 1 // 从下一个开始传
                        if(self.files[_file_item_index].merge_status != 'SUCCESS'){
                            self.upload(_file_item_index, _file_chun_index)
                        }
                    }
                }
            } else {
                this.$message.error('请选择要比对的ISO文件');
            }
        },
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
            self.oecp_task_id = cache.oecp_task_id
            if(self.step == 1){
                // 未上传完成，则重新选择文件，点击开始上传，会继续上传上次未完成上传的文件
                self.step = 0
                self.files = [
                    {progress: 0, filename: '', file: {}, size: 0, total_num: 0, chunk_num: 0, chunk_files: [], merge_task_id: 0, merge_status: 'PROGRESS'},
                    {progress: 0, filename: '', file: {}, size: 0, total_num: 0, chunk_num: 0, chunk_files: [], merge_task_id: 0, merge_status: 'PROGRESS'}
                ]
                self.status = 'PENDING'
                self.error_msg = ''
            } else if(self.step == 1) {
                for(var i = 0; i < 2; i++) {
                    let _file_index = JSON.parse(JSON.stringify(i))
                    if(self.files[_file_index].merge_status=='PROGRESS'){
                        self.get_progress_by_merge_task_id(_file_index, self.files[_file_index].merge_task_id)
                    } else {
                        self.upload(_file_index, self.files[_file_index].chunk_num + 1)
                    }
                }
            } else {
                for(var i = 0; i < 2; i++) {
                    let _file_index = JSON.parse(JSON.stringify(i))
                    if(self.files[_file_index].merge_status=='PROGRESS'){
                        self.get_progress_by_merge_task_id(_file_index, self.files[_file_index].merge_task_id)
                    } else {
                        // 都合并完了，
                        self.get_progress_by_oecp_task_id(self.oecp_task_id)
                    }
                }
            }
        },
        upload(_file_item_index, _slice_index){
            var self = this
            var item =  self.files[_file_item_index]
            // debugger
            console.log('upload' + _file_item_index + ':', _slice_index)
            let data = new FormData();
            // bolb文件流
            data.append("file", item.file.slice((_slice_index - 1) * self.slice_size, _slice_index * self.slice_size));
            // 文件名称 hash_索引
            data.append("filename", item.filename);
            // 文件名称 hash
            data.append("identifier", item.identifier);
            // 当前索引
            data.append("chunkNumber", _slice_index);
            // 总切片数
            data.append("total", item.total_num);
            // 文件总大小
            data.append("sze", item.size);
            self.$http.upload('upload/iso', data,
                (progressEvent) => {
                    let completeVal = ((progressEvent.loaded + (progressEvent.total * _slice_index)) / progressEvent.total / item.total_num) * 1000  || 0;
                    let _ptogress = parseFloat((parseInt(completeVal) / 10).toFixed(1))
                    self.files[_file_item_index].progress = _ptogress
                }
            ).then(res=>{
                if(res.data.code == '200'){
                    if(_slice_index >= self.files[_file_item_index].total_num) { // 全部上传成功
                        console.log('_slice_index', _slice_index)
                        console.log('upload success')
                        self.merge_files(_file_item_index, self.files[_file_item_index])
                        if(self.files[0].progress >= 100 && self.files[0].progress >= 100) { // 两个文件都上传完了，开始合并文件
                            self.step = 2
                        }
                    } else {
                        self.files[_file_item_index].chunk_num += 1
                        self.upload(_file_item_index, self.files[_file_item_index].chunk_num + 1)
                        // console.log('_slice_index', _slice_index)
                    }
                    self.set_upload_chunk_cache(item, item.chunk_num)
                    self.set_build_progress_cache()
                } else {
                    console.log('上传文件异常')
                    self.status = 'ERROR'
                    self.error_msg = res.data.message
                    self.clear_build_progress_cache()
                }
            })
        },
        /** 合并碎片文件 */
        async merge_files(file_item_index, file_item){
            var self = this
            self.$http.get(`upload/iso`, {filename: file_item.filename, identifier: file_item.identifier, totalChunks: file_item.total_num}).then(res=>{
                if (res.data.code === '200') { // 成功
                    self.files[file_item_index].merge_task_id = res.data.data
                    // self.step = 2
                    self.set_build_progress_cache()
                    self.get_progress_by_merge_task_id(file_item_index, res.data.data)
                } else {
                    console.log('合并文件异常')
                    self.status = 'ERROR'
                    self.error_msg = res.data.message
                    self.clear_build_progress_cache()
                }
            })
        },
        /**
         * 根据任务id查询合并任务进度
         */
        async get_progress_by_merge_task_id(file_index, merge_task_id){
            var self = this
            self.$http.get(`upload/async/state/${merge_task_id}`).then(res=>{
                if(res.data.code == '200'){
                    if(res.data.data.status == 'SUCCESS'){ // 合并完成
                        self.files[file_index].merge_status = 'SUCCESS'
                    }
                    if(self.files[0].merge_status == 'SUCCESS' && self.files[0].merge_status == 'SUCCESS') { // 两个文件都合并完了，开始生成报告
                        clearInterval(self.ticker)
                        self.build_oecp_report()
                    }
                    else if(res.data.data.status == 'PROGRESS'){
                        self.files[file_index].merge_status = 'PROGRESS'
                        setTimeout(() => {
                            self.get_progress_by_merge_task_id(file_index, merge_task_id)
                        }, self.ticker_time);
                    } else if(res.data.data.status == 'FAILED'){ // 合并失败
                        console.log('任务异常')
                        self.status = 'ERROR'
                        self.error_msg = res.data.message
                        self.clear_build_progress_cache()
                    }
                } else {
                    console.log('任务异常')
                    self.status = 'ERROR'
                    self.error_msg = res.data.message
                    self.clear_build_progress_cache()
                }
            })
        },
        /** 生成oecp报告 */
        async build_oecp_report(){
            var self = this
            self.$http.post('upload/analysis/iso',{
                source_iso: self.files[0].filename,
                target_iso: self.files[1].filename,
                title: self.files[0].filename + 'VS' + self.files[1].filename
            }).then(res=>{
                if (res.data.code === '200') { // 成功
                    self.oecp_task_id = res.data.data
                    self.set_build_progress_cache()
                    self.get_progress_by_oecp_task_id(res.data.data)
                } else {
                    console.log('合并文件异常')
                    self.status = 'ERROR'
                    self.error_msg = res.data.message
                    self.clear_build_progress_cache()
                }
            })
        },
        /**查询生成进度 */
        async get_progress_by_oecp_task_id(oecp_task_id){
            var self = this
            self.ticker = setInterval(async () => {
                var res = await self.$http.get(`upload/async/state/${oecp_task_id}`)
                // debugger
                if(res.data.code == '200'){
                    if(res.data.data.status == 'SUCCESS'){ // 全部完成
                        self.step = 4
                        clearInterval(self.ticker)
                        self.status = 'SUCCESS'
                        self.error_msg = ''
                        self.clear_build_progress_cache()
                    }
                    else if(res.data.data.status == 'PROGRESS'){
                        var result = res.data.data.result
                        if(result.finish == res.total){ // 解析完成,持久化中……
                            self.step = 3
                            clearInterval(self.ticker)
                        } else { // 解析中
                            self.step = 2
                        }
                        self.set_build_progress_cache()
                    } else if(res.data.data.status == 'FAILED'){ // 导入失败
                        var result = res.data.data.result
                        console.log('任务异常')
                        // self.step = 2
                        clearInterval(self.ticker)
                        self.status = 'ERROR'
                        self.error_msg = result.message
                        self.clear_build_progress_cache()
                        // 清除定时器
                    }
                }
            }, self.ticker_time);
        },
        /**
         * 设置上传切片缓存
         */
        set_upload_chunk_cache(file, chunk_num){
            localStorage.setItem(file.filename, chunk_num)
        },
        /**
         * 设置生成进度缓存
         */
        set_build_progress_cache(){
            var _cache = JSON.stringify({
                step: this.step,
                files: this.files,
                oecp_task_id: this.oecp_task_id,

                // action_id: this.action_id,
                status: this.status,
                error_msg: this.error_msg // 错误信息
            })
            localStorage.setItem('buid_progress', _cache)
        },
        /**
         * 清除缓存并将结果记录在操作记录缓存中
         */
        clear_build_progress_cache(){
            localStorage.removeItem('buid_progress')
            var _cache = {
                step: this.step,
                files: this.files,
                oecp_task_id: this.oecp_task_id,
                // action_id: this.action_id,
                status: this.status,
                error_msg: this.error_msg, // 错误信息
                date: dateFormat(new Date(), 'yyyy-MM-dd HH:mm:ss')
            }
            if(localStorage.getItem('build_history')){
                var history = JSON.parse(localStorage.getItem('build_history'))
                history.unshift(_cache)
                localStorage.setItem('build_history', JSON.stringify(history))
            } else {
                var history = [_cache]
                localStorage.setItem('build_history', JSON.stringify(history))
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
        width: 900px;
        margin: 0 auto;
    }
}
.tabview{
    width: 100%;
    text-align: center;
}
.uploadview{
    margin-top: 50px;
    .flieview{
        display: flex;
        width: 900px;
        margin: 0 auto;
        // justify-content: space-between;
        // vertical-align: middle;
        // padding: 0 100px;
        .item{
            width: 450px;
            .chooseview{

                display: flex;
                flex-flow: row;
                justify-content: space-around;
                vertical-align: middle;
            }
            .title{
                text-align: center;
                padding-top: 20px;
            }
        }
    }
    .actionview{
        padding: 50px 0;
        text-align: center;
    }
}
.dragger{
    width: 150px;
    height: 150px;
    padding: 20px 5px;
    display: inline-flex;
    flex-flow: column;
    justify-content: space-around;
    
    text-align: center;
    border: 1px solid black;
    border-style: dotted;
    background: #fafafa;
    &:hover{
        border-color: #1890ff;
        cursor: pointer;
    }
}
.input_file{
    display: none;
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
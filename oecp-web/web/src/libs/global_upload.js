export default {
    data() {
        return {
            step: 0,
            action_id: '',
            files: [
                {progress: 0, filename: '', file: {}, db_finish: 0, db_total: 0}
            ],
            status: 'PENDING', // ERROR,PENDING,SUCCESS
            error_msg: '', // 错误信息
            task_id: 0,
            ticker: null
        }
    },
    methods: {
        upload(_file) {
            // debugger
            var self = this
            var file = _file.file
            self.files = [{progress: 0, filename: file.name, file: file, db_finish: 0, db_total: 0}]
            self.action_id = uuid.v4().substring(0,8)
            self.step = 1
            var formData = new FormData();
            formData.append('title', file.name);
            formData.append('file', file);
            // const formData = new FormData()
            // debugger
            // formData.append('title', file.name)
            // formData.append('file', file)
            // var formData={
            //     title: file.name,
            //     file: file.originFileObj
            // }
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
                    if(res.data.data.status == 'PROGRESS'){
                        if(res.data.data.status == 'SUCCESS'){ // 解析完成
                            self.step = 3
                            self.status = 'SUCCESS'
                            clearInterval(self.ticker)
                        } else { // 解析中
                            var result = res.data.data.result
                            self.step = 2
                            // debugger
                            self.files[0].db_total = result.total
                            self.files[0].db_finish = result.finish
                            // if(result.total > 0) // 解析完成，正在做数据持久化
                        }
                    } else if(res.data.data.status == 'FAILURE'){ // 导入失败
                        self.step = 2
                        self.status = 'ERROR'
                        self.error_msg = res.data.message
                        clearInterval(self.ticker)
                    }
                } else {
                    console.log('查询任务进度异常')
                    self.status = 'ERROR'
                    self.error_msg = res.data.message
                    clearInterval(self.ticker)
                }
            }, 1000);
        },
        
        /**
         * 设置生成进度缓存
         */
        set_build_progress_cache(){
            localStorage.setItem('upload_progress',{
                step: this.step,
                files: this.files,
                task_id: this.task_id,

                action_id: this.action_id,
                status: this.status,
                error_msg: this.error_msg // 错误信息
            })
        },
    }
};
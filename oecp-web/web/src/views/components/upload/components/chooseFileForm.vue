<template>
    <div>
        <a-modal :visible="isShowForm" mask :maskClosable="false" scrollable title="选择要比对的ISO文件" :loading="loading" :footer="null" :width="619" @cancel="handleCancel">
            <a-spin :spinning="loading">
                <div style="width:100%;text-align:center">
                    <a-radio-group v-model="tab" button-style="solid" optionType="default">
                        <a-radio value="local">选择本地ISO文件</a-radio>
                        <a-radio value="server">选择已上传的ISO文件</a-radio>
                    </a-radio-group>
                </div>
                <div class="footer_view" v-if="tab=='local'">
                    <div class="action">
                        <a-button type="primary" @click="handleChooseFileFromLocal">确认</a-button>
                    </div>
                </div>
                <div class="footer_view" v-if="tab=='server'">
                    <a-table :data-source="iso_file_list" :columns="columns" rowKey="key" :pagination="false" :expandRowByClick="true" :loading="loading">
                        <template slot="index" slot-scope="text, row, index">
                            <span>{{(pageIndex - 1) * pageSize + index + 1}}</span>
                        </template>
                        <template slot="action" slot-scope="text, row">
                            <a-space>
                                <a-button type="danger" @click="handleDeleteServerFile(row)">删除</a-button>    
                                <a-button type="primary" @click="handleChooseFileFromServer(row)">确认选择</a-button>
                            </a-space>
                        </template>
                    </a-table>
                </div>
            </a-spin>
        </a-modal>
    </div>
</template>
<script>
export default {
    props: {
        isShowForm: {
            type: Boolean,
            default: false
        },
        FileItemIndex: {
            type: Number,
            default: 0
        }
    },
    data () {
        return {
            tab: 'local', // server
            loading: false,
            iso_file_list: [
                {file_name: 'openEuler-22.03-LTS-x86_64-dvd.iso'},
                {file_name: 'openEuler-20.03-LTS-SP3-x86_64-dvd.iso'}
            ], // 服务端ISO文件列表
            columns: [
                { title: "文件名", key:'file_name', dataIndex: "file_name"},
                { title: "操作", scopedSlots: { customRender: "action" }, width: 220, align: "center"}
            ],
        
        }
    },
    watch:{
        isShowForm(newval){
            if(newval) {
                this.init_iso_file_in_server()
            }
        }
    },
    methods: {
        init_iso_file_in_server() {
            var self = this
            this.$http.get('upload/storage/iso').then(res=>{
                self.iso_file_list = Object.keys(res.data.data).map(key=>({
                    key: key,
                    file_name: res.data.data[key]
                }))
            })
        },
        /**
         * 确认从本地上传
         **/
        handleChooseFileFromLocal(){
            this.$emit('confirmChooseFileFromLocal', {file_item_index: this.FileItemIndex})
        },
        /**
         * 确认从服务器选择文件
         */
        handleChooseFileFromServer(file) {
            this.$emit('confirmChooseFileFromServer',  {file_item_index: this.FileItemIndex, file_name: file.file_name})
        },
        handleUploadComplate(res){
            this.form.fileId = res.id
        },
        /** 删除服务器上已存在的iso文件 */
        handleDeleteServerFile(row) {
            var self = this
            this.$confirm({
                title: "删除iso文件",
                content: "您确定要删除服务器上已存在的iso文件吗?",
                okText: "确定",
                cancelText: "取消",
                onOk: () => {
                    self.$http.del(`upload/storage/iso?filename=${row.file_name}`).then(res=>{
                        if(res.data.code == '200'){
                            this.$message.success('删除成功')
                            self.init_iso_file_in_server()
                        } else {
                            self.$message.success(res.data.message)
                        }
                    })
                }
            });
        },
        handleCancel(){
            this.$emit('cancel')
        }
    }
}
</script>
<style lang="less" scoped>
.footer_view{
    margin-top: 20px;
    width: 100%;
    display: flex;
    flex-flow: column;
    text-align: center;
    justify-content: space-between;
    .action{
        width: 100%;
    }
}
</style>


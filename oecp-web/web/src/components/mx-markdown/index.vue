<template>
    <div class="markdown">
        <MarkdownPro ref="mdeditor" theme="dark" v-model="html" :autoSave="true" :interval="500" @on-upload-image="handleUploadImg" :toolbars="{uploadImage:true}" />
        <!-- <MarkdownPreview theme="dark" :initialValue="html"/> -->
    </div>
</template>
<script>
// 导入组件 及 组件样式
import { MarkdownPro, MarkdownPreview } from 'vue-meditor'
export default {
    // 注册
    components: {
        MarkdownPro,
        MarkdownPreview
    },
    props:{
        value:{
            type: String,
            default: ()=>{
                return ''
            }
        }
    },
    watch:{
        value(newval){
            this.html = newval
        },
        html(newval){
            this.$emit('change', newval)
            // this.value = this.html
        }
    },
    data() {
        return {
            html: ''
        }
    },
    methods:{
        // handleOnSave({value, theme}){
        //     console.log(this.html)
        //     // console.log(value, theme);
        // },
        handleUploadImg(file, callback){
            var self = this
            var _file = file
            console.log('上传处理器：', _file)
            const xhr = new XMLHttpRequest()
            xhr.withCredentials = false
            xhr.open('POST', self.$baseApiPath + "upload");
            xhr.setRequestHeader('Authorization', localStorage.getItem('token'))
            xhr.upload.onprogress = function (e) {
                // progress(e.loaded / e.total * 100)
            }

            xhr.onload = function () {
                if (xhr.status === 403 || xhr.status.code === 401) {
                self.$router.push('login')
                return
                }
                if (xhr.status != 200){
                failure('HTTP Error: ' + xhr.status)
                return
                }
                const json = JSON.parse(xhr.responseText)
                if (!json || typeof json.data.refPath !== 'string') {
                failure('Invalid JSON: ' + xhr.responseText)
                return
                }

                const file = json.data
                const url = file.refPath
                self.$refs.mdeditor.insertContent(`![image](` + url + `)`)

                // callback(url)
            }

            xhr.onerror = function () {
                failure('Image upload failed due to a XHR Transport error. Code: ' + xhr.status)
            }

            const formData = new FormData()
            formData.append('file', _file, _file.name)

            xhr.send(formData)
        }
    }
}
</script>

<template>
    <div style="display:flex;margin-top:5px">
        <div class='demo-upload-list' v-for="(item) in imageArray">
            <img :src='item'>
            <div class='demo-upload-list-cover'>
                <Icon type='ios-eye-outline' @click.native='handleView(item)'></Icon>
                <Icon type='ios-trash-outline' @click.native='handleRemove(item)'></Icon>
            </div>
        </div>
        <div @click="before_upload" class="ivu-upload ivu-upload-drag">
            <input @change="processFiles()" ref="uploader" multiple="multiple" accept="image/*" type="file" class="ivu-upload-input" />
            <slot>
                <div style="width: 60px; height: 60px; line-height: 60px;">
                    <i class="ivu-icon ivu-icon-ios-camera" style="font-size: 20px;"></i>
                </div>
            </slot>
        </div>
        <div style="margin-left:10px;color:#808695" v-if="tips">{{tips}}</div>
    </div>
</template>

<script>
export default {
    props: {
        id: {
            type: String,
            default: ''
        },
        multiple: {
            type: Boolean,
            default: false
        },
        tips:{
            type: String,
            default: ''
        },
        type:{
            type:String,
            default:'img'
        },
        images:{
            type: Array,
            default: []
        }
    },
    data() {
        return {
            imageArray:[]
        };
    },
    watch:{
        images(newVal){
            this.imageArray = newVal
        }
    },
    methods: {
        before_upload(e){
            e.currentTarget.firstElementChild.click()
        },
        processFiles(e){
            var files = this.$refs.uploader.files
            for(var i=0;i<files.length;i++){
                var file = files[i]
                var name = file.name;
                var extendName = name.substring(name.lastIndexOf('.'),name.length)
                let filename = 'a'+extendName
                var parseFile = new this.ParseServer.File(filename, file);
                parseFile.save().then(res=>{
                    debugger
                    if(res._url){
                        this.imageArray.push(res._url)
                        this.$emit('complate', this.imageArray); 
                    }
                })
            }
        },
        handleView(name) {
            this.$Modal.info({
                title: "查看图片",
                width: 800,
                content:
                "<div style='width:100%;height:100%;text-align:center'>" +
                "<img src='" +
                name +
                "'  style='max-width:100%;max-height:100%;padding-right:50px;display:inline-block'>" +
                "</div>",
                okText: "关闭"
            });
        },
        handleRemove(file) {
            const fileList = this.imageArray;
            this.imageArray.splice(fileList.indexOf(file), 1);
            this.$emit('complate', this.imageArray); 
        },
    },
    mounted() {
        this.imageArray = this.images
    }
};
</script>
<style scoped>
.demo-upload-list{
    display: inline-block;
    width: 60px;
    height: 60px;
    text-align: center;
    line-height: 60px;
    border: 1px solid transparent;
    border-radius: 4px;
    overflow: hidden;
    background: #fff;
    position: relative;
    box-shadow: 0 1px 1px rgba(0,0,0,.2);
    margin-right: 4px;
}
.demo-upload-list img{
    width: 100%;
    height: 100%;
}
.demo-upload-list-cover{
    display: none;
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(0,0,0,.6);
}
.demo-upload-list:hover .demo-upload-list-cover{
    display: block;
}
.demo-upload-list-cover i{
    color: #fff;
    font-size: 20px;
    cursor: pointer;
    margin: 0 2px;
}
</style>
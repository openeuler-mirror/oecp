<template>
  <div>
    <a-upload
      name="avatar"
      list-type="picture-card"
      class="avatar-uploader"
      :show-upload-list="false"
      :action="upload_action"
      :headers="headers"
      :before-upload="beforeUpload"
      :data="uploadfile"
      @change="handleChange"
    >
      <template v-if="imageUrl">
        <div class="imgview">
          <img :src="imageUrl " alt="avatar" :style="{width: (imgWidth>0?(imgWidth + 'px'): (100 + '%'))}" />
          <div class="editview" :style="{opacity: (loading ? 1 : 0)}">
            <a-icon v-if="loading" type="loading" />
            <a-icon v-else type="edit" />
          </div>
        </div>
      </template>
      <template v-else>
        <div>
          <a-icon v-if="loading" type="loading" />
          <a-icon v-else type="plus" />
          <div class="ant-upload-text">
            <!-- Upload -->
          </div>
        </div>
      </template>
    </a-upload>
    <div>{{tips}}</div>
  </div>
</template>
<script>
import { stringify } from 'qs';
export default {
  props: {
    imgWidth:{
      type: Number,
      default: 300
    },
    imgHeight:{
      type: Number,
      default: 0
    },
    url: {
      type: String,
      default: ''
    },
    tips: {
      type: String,
      default: ''
    }
  },
  watch:{
    url(newval){
      console.log(newval)
      if(newval){
        this.imageUrl = newval
      } else {
        this.imageUrl = ""
      }
    }
  },
  data() {
    return {
      loading: false,
      imageUrl: '',
      headers:{
        "Authorization": localStorage.getItem('token')
      },
      upload_action: this.$baseApiPath + "upload"
    };
  },
  mounted(){
    this.imageUrl = ""
  },
  methods: {
    uploadfile(file){
      console.log(this.$baseApiPath + "upload")
      return {file: file}
    },
    handleChange(info) {
      if(info.file && info.file.status && info.file.error && (info.file.error.status.code == 401 || info.file.error.status == 403)){ // token 过期
        this.$router.push('login')
        return
      }
      if (info.file.status === 'uploading') {
        this.loading = true;
        return;
      }
      if (info.file.status === 'done') {
        if(info.file.response.status.code == 401){
          this.$router.push('login')
          return
        }
        // debugger
        var _res = info.fileList[info.fileList.length - 1].response
        this.$emit("complate", {id: _res.data.id, url: _res.data.refPath})
        this.imageUrl = _res.data.refPath
        this.loading = false
        // getBase64(info.file.originFileObj, imageUrl => {
        //   this.imageUrl = imageUrl;
        //   this.loading = false;
        // });
      }
    },
    beforeUpload(file) {
      const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
      if (!isJpgOrPng) {
        this.$message.error('只能上传 JPG/png 格式!');
      }
      const isLt2M = file.size / 1024 / 1024 < 1;
      if (!isLt2M) {
        this.$message.error('图片必须小于 1MB!');
      }
      return isJpgOrPng && isLt2M;
    },
  },
};
</script>
<style>
.avatar-uploader > .ant-upload {
  min-width: 128px;
  min-height: 128px;
}
.ant-upload.ant-upload-select-picture-card{
  max-width: 100%;
  width: auto;
  height: auto;
}
.ant-upload-select-picture-card i {
  font-size: 32px;
  color: #999;
}

.ant-upload-select-picture-card .ant-upload-text {
  margin-top: 8px;
  color: #666;
}
.imgview{
  position: relative;
  width: 100%;
  height: 100%;
  left: 0;
}
.imgview img{
  position: relative;
  vertical-align: middle;
  max-width: 100%;
}
.imgview .editview{
  /* background-color: rgb(0,0,0 0.8); */
  opacity: 0;
  background: rgba(0,0,0,.6);
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  display: table;
}
.imgview:hover .editview{
  opacity: 1!important;
}

.imgview .editview i{
  position: relative;
  /* align-self: center; */
  vertical-align: middle;
  display: table-cell;
  /* top: 50%;
  margin-top: -16px; */
}
</style>
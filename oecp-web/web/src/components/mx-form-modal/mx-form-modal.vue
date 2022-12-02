<template>
    <a-modal :visible="isShowModal" mask :maskClosable="false" scrollable :title="title" :loading="loading" :width="width" :footer="null" @cancel="modalCancel">
        <!-- <div>
            <a-form :model="form" @submit="modalOk" :label-col="{ span: 7 }" :wrapper-col="{ span: 17 }" >
              <slot></slot>
              <a-form-item style="text-align:center">
                <a-button type="default" @click="modalCancel" style="margin-right:10px">
                  取消
                </a-button>
                <a-button type="primary" html-type="submit" style="margin-left:10px">
                  {{oktext}}
                </a-button>
              </a-form-item>
            </a-form>
        </div> -->
      <a-form-model  :label-col="labelCol" :wrapper-col="wrapperCol"
        :ref="form_ref"
        :model="form"
        :rules="mxrules"
      >
        <slot></slot>
        <div class="form-bottom"  v-if="!custom_buttons" :wrapper-col="{ span: 14, offset: 4 }" style="text-align:center">
          <a-button style="margin-right: 10px;" @click="modalCancel">取消</a-button>
          <a-button type="primary" style="margin-left:10px" :loading="loading" @click="modalOk">{{oktext}}</a-button>
        </div>
      </a-form-model>
    </a-modal>
</template>
<script>
export default {
  name: "MX_Form",
  props: {
    mxrules:{
      type: Object,
      default: {}
    },
    isShow: {
      type: Boolean,
      default: false,
    },
    oktext:{
        type: String,
        default: '提交'
    },
    width:{
        type:Number|String,
        default: '400'
    },
    title:{
      type: String,
      default: '',
    },
    form_ref: {
        type: String,
        default: 'form'
    },
    form:{
      type:Object,
      default: {}
    },
    custom_buttons:{
      type: Boolean,
      default: false
    }
  },
  data() {
    var self = this
    return {
      labelCol: { span: 7 },
      wrapperCol: { span: 17 },
      loading: false,
      isShowModal: false,
      // form: self.$form.createForm(this),
    };
  },
  mounted() {
    // this.$nextTick(() => {
    //   // this.form.validateFields();
    //   this.form.validateFields(['account_name'], { force: true });
    // });
  },
  methods: {
    modalOk(e){
        var self = this
        self.loading = true
        self.$refs[self.form_ref].validate(valid => {
            if (!valid) {
                this.$message.error('请检查您输入的表单')
                setTimeout(() => {
                    self.loading = false
                }, 100)
                return false
            } else {
              self.$emit('on-ok')
              setTimeout(() => {
                self.loading = false
              }, 100)
            }
        })
    },
    modalCancel(){
        this.$emit('on-cancel')
    },
    success(){
        this.loading = false
    },
    error(){
        var self = this
        self.loading = false
        setTimeout(() => {
            self.loading = true
        }, 100)
    }
  },
  watch: {
    isShow(newval){
      this.isShowModal = newval
    }
  }
};
</script>
<style>
</style>
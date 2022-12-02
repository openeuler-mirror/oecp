<template>
    <a-modal :visible="isShowModal" mask :maskClosable="false" scrollable :title="title" width="auto" :footer="null" @cancel="modalCancel">
        <div class="myImgDiv">
          <img v-if="src" :src="src"/>
        </div>
    </a-modal>
</template>
<script>
export default {
  name: "MX_Form",
  props: {
    isShow:{
        type: Boolean,
        default: false
    },
    src:{
      type: String,
      default: ''
    },
    width:{
        type:Number|String,
        default: '400'
    },
    title:{
      type: String,
      default: '',
    },
  },
  data() {
    var self = this
    return {
      labelCol: { span: 7 },
      wrapperCol: { span: 17 },
      loading: false,
      isShowModal: false,
    };
  },
  mounted() {
  },
  methods: {
    modalCancel(){
        this.$emit('cancel')
    },
  },
  watch: {
    isShow(newval){
      this.isShowModal = newval
    }
  }
};
</script>
<style scoped>
.myImgDiv {
  width:100%;
  padding: 20px;
  text-align:center;
}
.myImgDiv img{
  max-width: 100%;
  max-height: 100%;
}
</style>
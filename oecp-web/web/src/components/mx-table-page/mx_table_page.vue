<template>
  <div>
    <!-- <Table :ref="table_ref" :data="value" :columns="columns" :highlight-row="true" @on-current-change="handleSelectRow">
      <slot></slot>
    </Table> -->
    <slot></slot>
    <template v-if="isShowPage">
      <!-- <Page :total="total" :page-size="pageSize" :current="pageIndex" show-total  @on-change="changepage"></Page> -->
      <a-pagination show-quick-jumper show-size-changer
        :show-total="total => `共 ${total} 条数据`"
       :current="pageIndex" :pageSize="pageSize" :total="total" show-less-items @change="changepage" style="padding:20px 0;text-align:right"></a-pagination>
    </template>
  </div>
</template>
<script>
export default {
  name: 'mx_table',
  components: {
  },
  props: {
    pageIndex: {
      type: Number,
      default: 1
    },
    pageSize: {
      type: Number,
      default: 10
    },
    total: {
      type: Number,
      default: 1
    },
    isShowPage:{
      type: Boolean,
      default: true
    }
  },
  data () {
    return {
      // buttons: this.$route.meta.permissionInfos
    }
  },
  methods: {
    handleAction (methodsName) {
      if (methodsName) {
        // this.$emit(methodsName)
        if(this.$parent){
          this.$parent[methodsName]();
        }
      }
    },
    handleSelectRow (currentRow, oldCurrentRow) {
      this.$emit('on-current-change', currentRow)
    },
    changepage (index) {
      this.$emit('on-page-change', index)
    },
  },
  mounted () {
  },
  computed: {
  },
  watch: {
  }
}
</script>

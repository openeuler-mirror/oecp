<template>
    <div class="my-page">
      <mx-breadcrumb :list="route_list" />
      <div class="list_page_container">
            <div class="head">
                <div class="cardTitle">
                    <img class="icon" src="@/assets/img/divider.png"  alt='' />
                    <div style="padding-left:10px;font-weight: bold;font-size: 16px;">{{path}}</div>
                </div>
                <div class="right">
                    <a-space>
                        <a-icon type="rollback" style="color:#1890ff;line-height: 44px;height: 30px;" />
                        <div class="his_back" @click="handleGoBackClick">返回上一级</div>
                    </a-space>
                </div>
            </div>
            <div>
                <markdown-preview v-if="md_content" theme="dark" :initialValue="md_content"/>
            </div>
      </div>
    </div>
  </template>
  
  <script>
    import { MarkdownPreview } from 'vue-meditor'
  import MxTablePage from '@/components/mx-table-page'
  import MxSearchBox from '@/components/mx-search-box/mx_search_box.vue'
  import MxSearchBoxItem from '@/components/mx-search-box/mx-search-box-item.vue'
  import MxBreadcrumb from '@/components/mx-breadcrumb/index.vue'
  import moment from 'moment'
  export default {
      name: 'tables_page',
      components: {
          MxTablePage,
          MxSearchBox,
          MxSearchBoxItem,
          MxBreadcrumb,
          MarkdownPreview
      },
      data () {
          return {
              moment,
              route_list: [
                  {icon: 'home', title: '首页', route_path: 'index'},
                  {icon: 'appstore', title: '报告展示', route_path: 'home'},
                //   {icon: 'file', title: '比对详情'},
                  {icon: 'file', title: 'md详情'},
              ],
              report_base_id: 0,
              path: '',
              md_content: '',
              loading: false,
          }
      },
      computed: {
      },
      mounted() {
          var self = this
          self.path = self.$route.query.path
          if(self.$route.query.id) {
            self.report_base_id = self.$route.query.id
          }
          if(self.$route.query.path) {
            self.getData()
          }
      },
      methods: {
          handleGoBackClick(){
              this.$router.back()
          },
          handleSearch(){
  
          },
          changepage (index) {
              this.pageIndex = index
              this.getData()
          },
          getData () {
              var self = this
              self.loading = true
              self.$http.get(`report/md-detail/${self.report_base_id}?detail_path=${self.path}`).then(res=>{
                self.md_content = res.data.data.md_content
              },error=>{
                self.loading = false
              })
          },
      }
  }
  </script>
  
  <style lang="less" scoped>
  .breadcrumb{
    margin-left: 10px;
  }
  .chart{
    margin-left:10px;
    margin-top:20px;
  }
  .ant-descriptions-view{
    border-bottom: 0!important;
  }
  .ant-descriptions-view table tbody tr td, .ant-descriptions-view table tbody tr th{
    border-bottom: 1px solid #e8e8e8;
  }
  .link_btn{
      color: #1890ff;
      cursor: pointer;
  }
  
  .head{
    display: flex;
    justify-content: space-between;
    .cardTitle{
        display: flex;
        margin-bottom: 26px;
        padding-bottom: 13px;
        align-items: center;
        /* height: 40px; */
        border-bottom: 1px solid #E2EBFA;
    }
  }
  </style>
  
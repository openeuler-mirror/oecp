<template>
    <div>
        <mx-table-page :pageIndex="pageIndex" :pageSize="pageSize" :total="total" @on-page-change="changepage">
            <a-table :data-source="tables" :columns="columns" rowKey="id" :pagination="false" :expandRowByClick="true" :loading="loading" @change="handleChange">
                <template slot="md_detail" slot-scope="text, row">
                    <div class="link_btn" v-if="row.md_detail_path" @click="handleDetailClick(row)">
                        {{row.md_detail_path}}
                    </div>
                </template>
            </a-table>
        </mx-table-page>
    </div>
  </template>
  
  <script>
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
          MxBreadcrumb
      },
      data () {
          return {
              moment,
              compare_results: [],
              route_list: [
                  {icon: 'home', title: '首页', route_path: 'index'},
                  {icon: 'appstore', title: '报告展示', route_path: 'home'},
                  {icon: 'file', title: '比对详情'},
              ],
              search:{
                  compare_type: '',
                  compare_result: [],
                  category_level: '',
                  report_base_id: 0,
                  path: '',
                  order_by: '',
                  key_word: '',
                  order_by_mode: 'asc'
              },
              columns: [
                  {title: 'binary rpm package', key: 'rpm_package', dataIndex: 'rpm_package', sorter: true},
                  {title: 'source package', key: 'source', dataIndex: 'source', sorter: true},
                  {title: 'compare package', key: 'compare', dataIndex: 'compare', sorter: true},
                  {title: 'compare result', key: 'compare_result', dataIndex: 'compare_result', sorter: true},
                  {title: 'compare type', key: 'compare_type', dataIndex: 'compare_type', sorter: true},
                  {title: 'category level', key: 'category_level', dataIndex: 'category_level', sorter: true},
                  {title: 'details path', key: 'md_detail', scopedSlots: {customRender :'md_detail'}, sorter: true},  // 待定
              ],
              tables: [],
              loading: false,
              currRow: null,
              // 当前页数
              pageIndex: 1,
              // 每页显示多少条
              pageSize: 10,
              // 总条数
              total: 0,
          }
      },
      computed: {
      },
      methods: {
          handleGoBackClick(){
              this.$router.back()
          },
          handleDetailClick(row, type){
              var self = this
              let file_paths = row.md_detail_path.split('.')
              let file_type = file_paths[file_paths.length - 1]
              if(file_type == 'csv'){
                  this.$router.push({name: 'csv_detail', query:{
                      id: self.search.report_base_id,
                      path: row.md_detail_path
                  }})
              } else {
                  this.$router.push({name: 'md_detail', query:{
                      id: self.search.report_base_id,
                      path: row.md_detail_path
                  }})
              }
          },
          handleSearch(search){
                this.search = JSON.parse(JSON.stringify(search))
              this.pageIndex = 1
              this.getData()
          },
          changepage (index) {
              this.pageIndex = index
              this.getData()
          },
          /**
           * tableChange
           */
          handleChange(a, b, sorter){
              if(sorter.order){
                  this.search.order_by = sorter.columnKey
                  this.search.order_by_mode = sorter.order == 'ascend'?'asc':'desc'
              } else {
                  this.search.order_by = ''
                  this.search.order_by_mode = ''
              }
              this.getData()
          },
          getData () {
              var self = this
              self.loading = true
              self.$http.get(`report/detail/all-compare/page/${self.pageSize}/${self.pageIndex}`, {
                  compare_type: self.search.compare_type,
                  compare_result: self.search.compare_result.join('_'),
                  category_level: self.search.category_level,
                  report_base_id: self.search.report_base_id,
                  order_by: self.search.order_by,
                  key_word: self.search.key_word,
                  order_by_mode: self.search.order_by_mode,
                  path:  self.search.path.replace(/\s*/g, '')
              }).then(res=>{
                  self.loading = false
                  this.tables = JSON.parse(JSON.stringify(res.data.data.pages))
                  this.total = res.data.data.total
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
  
  
  .cardTitle{
      display: flex;
      margin-bottom: 26px;
      padding-bottom: 13px;
      align-items: center;
      /* height: 40px; */
      border-bottom: 1px solid #E2EBFA;
  }
  </style>
  
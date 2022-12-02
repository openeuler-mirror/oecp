<template>
    <div class="my-page">
      <mx-breadcrumb :list="route_list" />
      <div class="list_page_container">
          <div class="cardTitle">
              <img class="icon" src="@/assets/img/divider.png"  alt='' />
              <div style="padding-left:10px;font-weight: bold;font-size: 16px;">{{search.path}}</div>
          </div>
          <mx-search-box>
              <div slot="actionbox">
                  <a-space>
                      <a-icon type="rollback" style="color:#1890ff;line-height: 44px;height: 30px;" />
                      <div class="his_back" @click="handleGoBackClick">返回上一级</div>
                  </a-space>
              </div>
              <div slot="searchbox">
                   <mx-search-box-item title="compare type">
                      <a-select v-model="search.compare_type" style="width:200px">
                          <a-select-option key="all" value="">all</a-select-option>
                          <a-select-option v-for="(item, index) in compare_types" :key="index" :value="item.compare_type">{{item.compare_type}}</a-select-option>
                      </a-select>
                  </mx-search-box-item>
                  <mx-search-box-item title="compare result">
                      <a-select v-model="search.compare_result" placeholder="all" style="width:200px">
                          <a-select-option key="all" value="">all</a-select-option>
                          <a-select-option v-for="(item, index) in compare_results" :key="index" :value="item.compare_result">{{item.compare_result}}</a-select-option>
                      </a-select>
                      <div class="sel_tips">
                          <a-popover  slot="suffixIcon" placement="bottom">
                              <template slot="content">
                                  <p>1   -- same name + version + release num + distributor</p>
                                  <p>1.1 -- same name + version + release num</p>
                                  <p>2   -- same name + version</p>
                                  <p>3   -- same name</p>
                                  <p>4   -- less</p>
                                  <p>5   -- more</p>
                              </template>
                              <template slot="title">
                                  <span>compare result说明</span>
                              </template>
                              <a-icon type="eye" />
                          </a-popover>
                      </div>
                  </mx-search-box-item>
                  <mx-search-box-item title="category level">
                      <a-select v-model="search.category_level" style="width:200px">
                          <a-select-option key="all" value="">all</a-select-option>
                          <a-select-option key="0" value="0">0</a-select-option>
                          <a-select-option key="1" value="1">1</a-select-option>
                          <a-select-option key="2" value="2">2</a-select-option>
                          <a-select-option key="3" value="3">3</a-select-option>
                          <a-select-option key="4" value="4">4</a-select-option>
                          <a-popover  slot="suffixIcon" placement="bottom">
                              <template slot="content">
                                  <p>Level 0：核心包</p>
                                  <p>Level 1：软件包及软件包 API、ABI 在某个 LTS 版本的生命周期保持不变，跨 LTS 版本不保证</p>
                                  <p>Level 2：软件包及软件包 API、ABI 在某个 SP 版本的生命周期保持不变，跨 SP 版本不保证</p>
                                  <p>Level 3：版本升级兼容性不做保证</p>
                                  <p>Level 4：未指定包等级</p>
                              </template>
                              <template slot="title">
                                  <span>category level说明</span>
                              </template>
                              <a-icon type="eye" />
                          </a-popover>
                      </a-select>
                  </mx-search-box-item>
                  <mx-search-box-item>
                      <a-button type="primary" @click="handleSearch" icon="search">搜索</a-button>
                  </mx-search-box-item>
              </div>
          </mx-search-box>
          <mx-table-page :pageIndex="pageIndex" :pageSize="pageSize" :total="total" @on-page-change="changepage">
              <a-table :data-source="tables" :columns="columns" rowKey="id" :pagination="false" :expandRowByClick="true" :loading="loading" @change="handleChange">
                  <template slot="abi_detail" slot-scope="text, row">
                      <div class="link_btn" v-if="row.detail_path" @click="handleDetailClick(row)">
                          {{row.detail_path}}
                      </div>
                  </template>
              </a-table>
          </mx-table-page>
      </div>
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
              compare_types: [],
              compare_results: [],
              route_list: [
                  {icon: 'home', title: '首页', route_path: 'index'},
                  {icon: 'appstore', title: '报告展示', route_path: 'home'},
                //   {icon: 'file', title: '比对详情'},
                  {icon: 'file', title: 'service详情'},
              ],
              search:{
                  compare_type: '',
                  compare_result: '',
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
                  {title: 'file path', key: 'file_name', dataIndex: 'file_name', sorter: true},  // 待定
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
      mounted() {
          var self = this
          self.search.report_base_id = this.$route.query.id
          self.search.path = this.$route.query.path
          self.$http.get(`report/compare/all-compare-type/${self.search.report_base_id}?key=diffservice`).then(res=>{
              self.compare_types = res.data.data
          })
          self.$http.get(`report/compare/all-compare-result/${self.search.report_base_id}?key=diffservice`).then(res=>{
              self.compare_results = res.data.data
          })
          self.getData()
      },
      methods: {
          handleGoBackClick(){
              this.$router.back()
          },
          handleDetailClick(row, type){
              var self = this
              this.$router.push({name: 'md_detail', query: {
                      report_base_id: self.search.report_base_id
                  },  params: {
                      path: row.compare_detail
                  }
              })
          },
          handleSearch(){
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
              self.$http.get(`report/diff-service-csv-detail/page/${self.pageSize}/${self.pageIndex}`, {
                  compare_type: self.search.compare_type,
                  compare_result: self.search.compare_result,
                  report_base_id: self.search.report_base_id,
                  order_by: self.search.order_by,
                  order_by_mode: self.search.order_by_mode,
                  path: self.search.path
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
  
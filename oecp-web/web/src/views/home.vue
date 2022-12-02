<template>
    <div class="my-page">
        <mx-breadcrumb :list="route_list" />
      <a-spin :spinning="loading">
          <div class="list_page_container">
              <a-tabs v-model="level" @change="tab_change">
                  <a-tab-pane key="ALL" tab="全量软件包"></a-tab-pane>
                  <a-tab-pane key="L1" tab="L1软件包"></a-tab-pane>
                  <a-tab-pane key="L2" tab="L2软件包"></a-tab-pane>
              </a-tabs>
              <div class="chart" v-show="selectedRowKeys && selectedRowKeys.length > 0">
                  <a-row type="flex">
                      <a-col :span="12">
                          <chart1 ref="chart1" />
                      </a-col>
                      <a-col :span="12">
                          <div style="text-align:right">
                              <chart2 ref="chart2" />
                          </div>
                      </a-col>
                  </a-row>
              </div>
              <div style="margin-top:20px">
                  <mx-table-page :pageIndex="pageIndex" :pageSize="pageSize" :total="total" @on-page-change="changepage">
                      <a-table :data-source="tables" :columns="columns" rowKey="id" :row-selection="{selectedRowKeys: selectedRowKeys,onChange: onSelectChange}" :expanded-row-keys.sync="expandedRowKeys" :pagination="false" :expandRowByClick="true" :loading="loading">
                          <template slot="index" slot-scope="text, row, index">
                              <span>{{(pageIndex - 1) * pageSize + index + 1}}</span>
                          </template>
                          <template slot="version" slot-scope="text, row">
                              <div v-if="row.isEdit" style="display:flex;">
                                  <a-input v-model="row.version_txt" />
                                  <a-button type="primary" style="margin: 0 10px" @click="handleSaveVersion(row)">保存</a-button>
                                  <a-button @click="row.isEdit=false;row.version_txt=row.version">取消</a-button>
                              </div>
                              <div v-else class="version">
                                  <a-space>
                                      {{ row.version }}
                                      <a-button @click="row.isEdit=true">编辑</a-button>
                                  </a-space>
                              </div>
                          </template>
                          <template slot="r_delete" slot-scope="text, row">
                              <a-button @click="handleDetailClick(row, 'r_delete')" type="link">
                                  {{text}}
                              </a-button>
                          </template>
                          <template slot="r_add" slot-scope="text, row">
                              <a-button @click="handleDetailClick(row, 'r_add')" type="link">
                                  {{text}}
                              </a-button>
                          </template>
                          <template slot="r_release" slot-scope="text, row">
                              <a-button @click="handleDetailClick(row, 'r_release')" type="link">
                                  {{text}}
                              </a-button>
                          </template>
                          <template slot="version_update" slot-scope="text, row">
                              <a-button @click="handleDetailClick(row, 'version_update')" type="link">
                                  {{text}}
                              </a-button>
                          </template>
                          <template slot="consistent" slot-scope="text, row">
                              <a-button @click="handleDetailClick(row, 'consistent')" type="link">
                                  {{text}}
                              </a-button>
                          </template>
                          <template slot="provide_change" slot-scope="text, row">
                              <a-button @click="handleDetailClick(row, 'provide_change')" type="link">
                                  {{text}}
                              </a-button>
                          </template>
                          <template slot="require_change" slot-scope="text, row">
                              <a-button @click="handleDetailClick(row, 'require_change')" type="link">
                                  {{text}}
                              </a-button>
                          </template>
                          <template slot="actions" slot-scope="text, row">
                              <a-space v-if="!row.isDeling">
                                  <a-button type="primary" @click="handleReportDetail(row)">查看报告</a-button>
                                  <a-button type="danger" @click="handleDelete(row)" >删除</a-button>
                              </a-space>
                              <a-space v-else>
                                  <a-icon type="loading" />
                                  <span>删除中……</span>
                              </a-space>
                          </template>
                      </a-table>
                  </mx-table-page>
              </div>
          </div>
      </a-spin>
    </div>
  </template>
  
  <script>
  import 'ant-design-vue'
  import MxTablePage from '@/components/mx-table-page'
  import {tool} from '@/libs/util'
  // import echartCard from '@/components/chart/echart_card'
  import chart1 from './components/home/Chart_1.vue'
  import chart2 from './components/home/Chart_2.vue'
  import MxBreadcrumb from '@/components/mx-breadcrumb/index.vue'
  import moment from 'moment'
  export default {
      name: 'tables_page',
      components: {
          MxTablePage,
          MxBreadcrumb,
          // echartCard,
          chart1,
          chart2,
      },
      data () {
          return {
              moment,
              level: 'ALL',
              selectedRowKeys: [],
              
                route_list: [
                    {icon: 'home', title: '首页', route_path: 'index'},
                    {icon: 'appstore', title: '报告查询'}
                ],
              columns: [
                  {title: '版本', key: 'version',scopedSlots: {customRender :'version'}, align: 'left'},
                  {title: '删除', key: 'r_delete',scopedSlots: {customRender :'r_delete'}, dataIndex: 'r_delete', width: 100},
                  {title: '新增', key: 'r_add',scopedSlots: {customRender :'r_add'}, dataIndex: 'r_add', width: 100},
                  {title: 'release', key: 'r_release',scopedSlots: {customRender :'r_release'}, dataIndex: 'r_release', width: 100},
                  {title: '版本升级', key: 'version_update',scopedSlots: {customRender :'version_update'}, dataIndex: 'version_update', width: 100},
                  {title: '保持一致', key: 'consistent',scopedSlots: {customRender :'consistent'}, dataIndex: 'consistent', width:100},
                  {title: 'provide变化', key: 'provide_change',scopedSlots: {customRender :'provide_change'}, dataIndex: 'provide_change', width: 130},
                  {title: 'require变化', key: 'require_change',scopedSlots: {customRender :'require_change'}, dataIndex: 'require_change', width: 130},
                  {title: '操作', key: 'actions', scopedSlots: {customRender :'actions'}, width: 150}
              ],
              expandedRowKeys:[],
              tables: [],
              loading: false,
              del_loading: false,
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
          self.getData()
          window.onresize = () => {
              this.$refs["chart1"].onresize()
              this.$refs["chart2"].onresize()
          }
      },
      methods: {
          handleDetailClick(row, type){
              if(row.isDeling == true){
                  this.$message.error('正在删除中，请查看其他报告');
                  return 
              }
              let c_level = ''
              if(this.level == 'L1') {
                  c_level = 1
              } else if(this.level == 'L2'){
                  c_level = 2
              }
              let c_type = 'rpm package name'
              if(type == 'provide_change') {
                  c_type = 'rpm provides'
              }
              if(type == 'require_change'){
                  c_type = 'rpm requires'
              }
              this.$router.push({name: 'all_rpm_report', query:{
                  r_bid: row.report_base_id,
                  a_type: type,
                  c_type: c_type,
                  c_level: c_level
              }})
          },
          tab_change(tab) {
              this.pageIndex = 1
              this.getData()
          },
          changepage (index) {
              this.pageIndex = index
              this.getData()
          },
          onSelectChange(selectedRowKeys, selectedRows) {
              var self = this
              self.selectedRowKeys = selectedRowKeys
              if(self.$refs.chart1 && self.$refs.chart2) {
                  self.$refs.chart1.on_data_change(selectedRows)
                  self.$refs.chart2.on_data_change(selectedRows)
              }
          },
          getData () {
              var self = this
              self.loading = true
              self.$http.get(`report/page/${self.pageSize}/${self.pageIndex}`,{level: self.level}).then(res=>{
                  self.loading = false
                  var _selectedRowKeys = []
                  var _selectedRows = []
                  if(res.data.data) {
                      var list = []
                      res.data.data.pages.forEach((item, index) => {
                          if(index < 5) {
                              _selectedRowKeys.push(item.id)
                              _selectedRows.push(item)
                          }
                          item.isEdit = false
                          item.isDeling = (item.state == 'deleting')
                          item.version_txt = item.version
                          list.push(item)
                      })
                      self.selectedRowKeys = _selectedRowKeys
                      if(self.$refs.chart1 && self.$refs.chart2) {
                          self.$refs.chart1.on_data_change(_selectedRows)
                          self.$refs.chart2.on_data_change(_selectedRows)
                      }
                      self.tables = JSON.parse(JSON.stringify(list))
                      self.total = res.data.data.total
                  }
              },error=>{
                  self.loading = false
              })
          },
          /** 保存版本标题 */
          handleSaveVersion(row) {
              var self = this
              if(row.version_txt){
                  self.$http.post(`report/update-version/${row.report_base_id}`,{version: row.version_txt}).then(res=>{
                      if(res.data.code == '200'){
                          self.$message.success('保存成功');
                          self.getData()
                      }
                      console.log(res)
                  })
              } else {
                  self.$message.error('版本标题不能为空！');
              }
          },
          /** 查看报告总览 */
          handleReportDetail(row){
              this.$router.push({name: 'report_detail', query:{
                  report_base_id: row.report_base_id
              }})
          },
          /** 删除报告信息 */
          handleDelete(row) {
              var self = this
              this.$confirm({
                  title: '删除确认',
                  content: '确定要删除当前数据吗？',
                  okText: '确定',
                  cancelText: '取消',
                  onOk: () => {
                      row.isDeling = true
                      self.del_loading = true
                      self.$http.del(`report/update-version/${row.report_base_id}`).then(res=>{
                          self.del_loading = false
                          if(res.data.code == '200'){
                              self.$message.success('删除成功！');
                              self.getData()
                          }
                          console.log(res)
                      })
                  }
              })
          }
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
  .version{
      cursor: default;
      .ant-btn{
          display: none;
      }
      &:hover .ant-btn{
          display: inline-block;
      }
  }
  </style>
  
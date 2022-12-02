import Vue from 'vue'
import App from './App.vue'
import router from './router'
// import './util/AntDesign'
import 'ant-design-vue/dist/antd.css'
import '@/assets/css/index.css'
import moment from 'moment'
import http from '@/libs/http'
import config from '@/config'
import 'ant-design-vue'
import 'ant-design-vue/dist/antd.css'
import { message } from 'ant-design-vue'
import '@/core/lazy_use'

// 引入基本模板
Vue.config.productionTip = false

Vue.prototype.$message = message
Vue.prototype.$config = config
Vue.prototype.$http = http
// Vue.prototype.$echarts = echarts
const baseApiUrl = process.env.VUE_APP_API_BASE_URL
Vue.prototype.$baseApiPath = baseApiUrl


console.log('env', process.env)


Vue.filter('filterTime', (value) => {
  moment.locale('zh-cn') // 使用中文
  // 判断当前日期是否是7天之前
  if (moment(value).isBefore(moment().subtract(7, 'days'))) {
    return moment(value).format('YYYY-MM-DD')
  } else {
    // 1小时前
    return moment(value).from(moment())
  }
})

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')

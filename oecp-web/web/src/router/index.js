import Vue from 'vue'
import Router from 'vue-router'
import routes from './routers'
import config from '@/config'

Vue.use(Router)
const router = new Router({
    routes,
    mode: 'hash',// history, hash
    base: config.virtualDir
})
router.beforeEach((to, from, next) => {
  if(to.name=='layout'){
    router.push({name:'index'})
  } else {
    next()
  }
})
router.afterEach(to => {
    // antDesignVue.LoadingBar.finish()
    // window.scrollTo(0, 0)
})

export default router
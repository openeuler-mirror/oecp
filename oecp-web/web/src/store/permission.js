// import { constantRouterMap } from '@/router'
import constantRouterMap from '@/router/routers'
import lazyLoading from '@/libs/lazyLoading'
import Main from '@/views/layout'
import parentView from '@/components/parent-view'
import { setToken, getToken } from '@/libs/util'

function GenerateMenu (menus, item) {
  if (item) {
    var menu = {
      path: item.path,
      component: Main,
      redirect: item.redirect,
      name: item.name,
      permissionInfos: item.permissionInfos,
      meta: { title: item.meta.title, icon: item.meta.icon, hideInMenu: item.meta.hideInMenu, permissionInfos: item.permissionInfos  }
    }
    AddChildrenMenu(item, menu)
    menus.push(menu)
  }
}

function AddChildrenMenu (item, menu) {
  if (item.children && item.children.length) {
    menu.children = []
    item.children.filter(chd => {
      // console.log(chd);
      if (chd) {
        var cMenu = {
          path: chd.path,
          component: chd.component === 'parentView' ? parentView : lazyLoading(chd.href),
          name: chd.name,
          permissionInfos: chd.permissionInfos,
          meta: { title: chd.meta.title, icon: chd.meta.icon, hideInMenu: chd.meta.hideInMenu, permissionInfos: chd.permissionInfos }
        }
        AddChildrenMenu(chd, cMenu)
        // console.log(cMenu)
        menu.children.push(cMenu)
      }
    })
  }
}

const permission = {
  state: {
    routers: constantRouterMap,
    addRouters: [],
    currRoute: null
  },
  mutations: {
    SET_ROUTERS: (state, routers) => {
      state.addRouters = routers
      state.routers = constantRouterMap.concat(routers)
    },
    SET_CURR_ROUTER: (state, currRoute) => {
      state.currRoute = currRoute
    },
  },
  actions: {
    
   
    GenerateRoutes ({ commit }, data) {
      return new Promise(resolve => {
        const { modules } = data
        const accessedRouters = []
        if (modules && modules.length > 0) {
          var menus = modules[0].children
          if (menus && menus.length > 0) {
            menus.filter(item => {
              GenerateMenu(accessedRouters, item)
            })
          }
        }
        commit('SET_ROUTERS', accessedRouters)
        resolve()
      })
    },
    ClearRoutes ({commit}) {
      const accessedRouters = []
      commit('SET_ROUTERS', accessedRouters)
    },
    SetCurrRoute({commit},to) {
      commit('SET_CURR_ROUTER',  to)
    },
  }
}

export default permission

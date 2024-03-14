# OECP报告展示前端详细设计

#### 1、设计概述

​	    OECP报告展示系统前端整体采用vue框架搭建，使用Ant design Vue前端组件库进行页面功能的开发。

#### 2、总体方案

​	    项目整体技术栈基于JavaScript ES2015+。主要引用的外部库包括：Vue.js、Vuex、Vue-Router、Ant design Vue、Axios等。技术栈架构图如下图所示：

![前端技术架构图](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF%E6%8A%80%E6%9C%AF%E6%9E%B6%E6%9E%84%E5%9B%BE.jpg)

​		Vue.js框架是一套响应式前端框架，可支持组件化开发，是本系统视图层采用的主体框架。该框架提供了对Html视图和数据接口之间的动态双向绑定能力，极大简化了视图层的开发工作。同时基于Ant Design Vue基础UI组件库进行系统的开发。

​		本系统为前端单页面应用，采用Vue-Router进行页面路由管理。由Vue-Router统一对页面URL进行监控，再根据访问路径渲染不同的页面进行展示。本系统页面数据均通过axios从后端接口获取。使用Vuex进行路由状态管理。

#### 3、详细设计

##### 	3.1 程序目录结构

| 一级目录          | 二级目录   | 说明                                                   |
| ----------------- | ---------- | ------------------------------------------------------ |
| node_modules      |            | 包含node运行时的基础依赖包。                           |
| public            |            | 包含html入口文件，公共样式文件，字体文件icon图标文件。 |
| src               | assets     | 包含静态资源文件：图片、图标、字体、样式文件等         |
|                   | components | 前端页面自定义的公用组件                               |
|                   | config     | 包含整个项目运行时的配置文件                           |
|                   | core       | 包含引入antd-vue组件库的配置                           |
|                   | libs       | 包含封装的前端公共方法，和请求后端接口的方法           |
|                   | router     | 包含路由规则和配置的路由地址文件                       |
|                   | store      | 包含框架自带状态管理文件和封装的部分状态管理方法。     |
|                   | views      | 包含前端页面文件，自定义页面组件等                     |
|                   | App.vue    | 页面入口文件                                           |
|                   | main.js    | 程序入口文件，加载各种公共组件                         |
| .env              |            | 环境变量文件                                           |
| .gitignore        |            | Git上传需要忽略的文件格式                              |
| babel.config.js   |            | 前端JavaScript兼容性插件配置                           |
| default.conf      |            | nginx配置文件                                          |
| Dockerfile        |            | 自动化部署相关配置                                     |
| package-lock.json |            | 锁定安装时的包的版本号，保证大家使用的依赖包版本一致   |
| package.json      |            | 项目基本信息,包依赖信息等                              |
| README.md         |            | 项目说明                                               |
| vue.config.js     |            | 整个项目运行配置                                       |

##### 3.2 路由模块说明

​		系统是基于Vue官方路由Vue-Router实现的前端单页面应用。即不论URL路径如何切换，系统始终都是访问同一个Html文件。路由模块在实际运行时监控URL路径的变化。根据新的URL路径加载对应的页面组件，并对原页面进行更新。

​		本系统中的主要路由配置在src/router/routers.js文件中，path代表要跳转的路由地址，name表示路由名称，meta中可以配置一些自定义的额外参数，component表示该路由指向的页面组件。整个路由表配置如下：

```
{
    path: '/',
    name: 'home',
    meta: {title:'首页', icon:'home'},
    component: () => import('@/views/layout'),
    children: [
      {
        path: '/index',
        name: 'index',
        meta: {title:'首页', icon:'home'},
        component: () => import('@/views/index'),
      },
      {
        path: '/upload',
        name: 'upload',
        meta: { title: '上传', icon: 'cloud-upload-outlined' },
        component: () => import('@/views/upload'),
      },
      {
        path: '/report_detail',
        name: 'report_detail',      
        meta: { title: '报告总览' },
        component: () => import('@/views/report_detail.vue'),
      },
      {
        path: '/all_rpm_report',
        name: 'all_rpm_report',      
        meta: { title: '报告详情' },
        component: () => import('@/views/all_rpm_report.vue'),
      },
      {
        path: '/change_detail',
        name: 'change_detail',      
        meta: { title: '变更详情' },
        component: () => import('@/views/change_detail.vue'),
      },
      {
        path: '/compare_detail',
        name: 'compare_detail',      
        meta: { title: '比对详情' },
        component: () => import('@/views/compare_detail.vue'),
      },
      {
        path: '/abi_detail',
        name: 'abi_detail',      
        meta: { title: 'abi详情' },
        component: () => import('@/views/abi_detail.vue'),
      },
    ]
}
```

##### 3.3 页面说明

​		所有页面文件都在src/views目录下。其中较为独立的功能块或和重复使用的功能块归纳提取为页面组件存放于src/views/components目录下，方便开发和调试。主要功能页面文件设计如下表：

| 路由            | 文件路径                     | 说明                                                         |
| --------------- | ---------------------------- | ------------------------------------------------------------ |
| /home           | src/views/layout.vue         | 整个应用总体布局文件，包含页面顶部标题和布局样式等           |
| /index          | src/views/index.vue          | 首页功能模块,包含所有报告总览信息、统计图表等                |
| /report_detail  | src/views/report_detail.vue  | 单份报告的总览信息，以及报告各个指标下的统计信息，统计图表等 |
| /all_rpm_report | src/views/all_rpm_report.vue | 单份报告详情列表，可分页查询单份报告所有比对项的比对结果信息 |
| /change_detail  | src/views/change_detail.vue  | 单份报告变更详情，可分页查询单份报告所有变更详情信息         |
| /compare_detail | src/views/change_detail.vue  | 单份报告比对结果详细信息，可分页查询单份报告比对结果的详细信息 |
| /abi_detail     | src/views/abi_detail.vue     | abi比对详情信息，显示存在abi比对详情的md文档信息             |

###### 	3.3.1 首页

​		首页包含报告总览信息，统计图表等，具体原型如下图所示，【标记1】处的tab组件可实现切换需要统计的软件包级别，包含全量软件包、L1软件包、L2软件包。切换后【标记2】和【标记3】处会根据软件包级别切换不同的统计内容。【标记2】处会显示相应软件包级别对应的统计图表。【标记3】处会分页显示软件包具体统计数据。同时【标记3】处列表第一列多选框可实现切换【标记2】处统计图表数据。

![前端-首页](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF-%E9%A6%96%E9%A1%B5.png)

###### 	3.3.2 上传报告

​		上传报告页面主要实现点击选择报告上传（或拖拽报告至上传区域实现上传）功能，可查看上传进度。如下图所示：

![前端-上传报告](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF-%E4%B8%8A%E4%BC%A0%E6%8A%A5%E5%91%8A1.png)

###### 	3.3.3 生成报告

​		生成报告主要实现点击选择ISO文件（或拖拽ISO文件）上传，或选择已上传ISO文件。点击开始上传生成报告、解析报告并完成报告持久化存贮。如下图所示：

![前端-生成报告](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF-%E7%94%9F%E6%88%90%E6%8A%A5%E5%91%8A.png)

###### 	3.3.4 报告总览

​		报告总览页面展示单个报告的依据软件包兼容性等级进行的文件统计、服务文件统计、命令文件统计、配置文件统计、接口文件统计、ABI变更统计及OSV技术测评报告等信息，如下图所示：

![前端-报告总览](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF-%E6%8A%A5%E5%91%8A%E6%80%BB%E8%A7%88.png)

###### 	3.3.5 报告详情

​		报告详情页实现查询显示按条件查询单个报告详细信息。如下图所示：

![前端-报告详情](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF-%E6%8A%A5%E5%91%8A%E8%AF%A6%E6%83%85.png)

###### 	3.3.6 变更详情

​		变更详情页实现按条件分页查询单个报告所有变更项列表，具体功能如下图所示：

![前端-变更详情](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF-%E5%8F%98%E6%9B%B4%E8%AF%A6%E6%83%85.png)

###### 	3.3.7 比对详情

​		比对详情页实现按条件分页查询单个报告所有比对项详细列表，具体功能如下图所示：

![前端-比对详情](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF-%E6%AF%94%E5%AF%B9%E8%AF%A6%E6%83%85.png)

###### 	3.3.8 abi详情

​		abi详情页可查看单个比对报告中的动态库abi变更详细信息，如下图所示：

![前端-abi详情](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF-abi%E8%AF%A6%E6%83%85.png)

##### 3.4 数据请求模块说明

​		数据请求模块将Axios实例对象封装为http对象。通过http对象将Axios的相关方法和请求信息（URL地址、请求参数）统一封装成get、post、delete方法，各业务模块通过请求相关方法实现发送请求到后端api，获取请求结果并展示到相应页面和组件。

​		http对象调用后端api后返回一个Promise异步对象，通过Promise对象在业务代码中对请求返回结果配置回调处理方法（.then()），其中res对象表示接口请求正确后返回的对象，error表示接口请求出错后返回的对象。

​		基于vue的全局属性，将http对象配置为系统全局属性$http属性，在需要调用后端api地址时直接使用this.$http表示http对象，具体使用方式如下所示：

```
this.$http.get('后端API接口地址', {
	// 后端API接口参数
}).then(res=>{
   	// 后端接口请求成功后返回 res 对象
},error=>{
	// 接口请求错误后返回的错误对象error
})
```

##### 3.5 系统启动加载顺序

![前端-启动顺序](https://gitee.com/yang-yulong-007/img_bed/raw/master/oecp_web_imgs/%E5%89%8D%E7%AB%AF-%E5%90%AF%E5%8A%A8%E9%A1%BA%E5%BA%8F.png)

- 系统首先会执行public/index.html文件
- 接着会执行src/main.js文件
- 由于main.js挂载了app.vue文件，系统接着会使用app.vue的templete替换index.html中的id为app的div
- 接着系统会将已注入到main.js的路由文件对应的组件渲染到router-view中
- router-view开始加载layout.vue文件
- layout.vue加载首页或其他相应页面模块
- 更新DOM并显示页面内容

##### 3.6 其他说明

​	3.6.1 前端持久化存储说明

​		前端根据业务主要采用localStorage用来保存临时状态数据

​	3.6.2 启动说明

​		系统开发采用node v14.17.3版本，启动前需要先安装package.json中配置的依赖插件，之后才可启动或者编译。具体命令如下：

系统插件安装命令：

```
npm install
```

系统启动命令：

```
npm run serve
```

系统编译命令：

```
npm run build
```
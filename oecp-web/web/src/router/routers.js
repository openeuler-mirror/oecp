import Vue from "vue";
import VueRouter from "vue-router";

Vue.use(VueRouter);

const routes = [
    {
      path: '/',
      name: 'index',
      meta: {title:'首页', icon:'home'},
      component: () => import('@/views/index'),
    },
    {
        path: '/layout',
        name: 'layout',
        meta: {title:'布局文件', icon:'layout'},
        component: () => import('@/views/layout'),
        children: [
        {
            path: '/home',
            name: 'home',
            meta: {title:'报告查询', icon:'home'},
            component: () => import('@/views/home'),
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
            path: '/difference_detail',
            name: 'difference_detail',      
            meta: { title: '变更详情' },
            component: () => import('@/views/difference_detail.vue'),
        },
        {
            path: '/file_report',
            name: 'file_report',      
            meta: { title: '文件统计详情' },
            component: () => import('@/views/file_report.vue'),
        },
        {
            path: '/compare_detail',
            name: 'compare_detail',      
            meta: { title: '比对详情' },
            component: () => import('@/views/compare_detail.vue'),
        },
        {
            path: '/csv_detail',
            name: 'csv_detail',      
            meta: { title: 'service详情' },
            component: () => import('@/views/csv_detail.vue'),
        },
        {
            path: '/md_detail',
            name: 'md_detail',      
            meta: { title: 'service详情' },
            component: () => import('@/views/md_detail.vue'),
        },
        ]
    },
];
export default routes;

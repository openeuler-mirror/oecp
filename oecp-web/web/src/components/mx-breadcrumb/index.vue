<template>
    <div>
        <a-breadcrumb>
            <a-breadcrumb-item v-for="item in list" :key="item.path">
                <span @click="hanldeHistoryClick(item)">
                    <a-space :class="[item.route_path? 'breadcrumb_item': '']">
                        <a-icon v-if="item.icon" :type="item.icon" />{{item.title}}
                    </a-space>
                </span>
            </a-breadcrumb-item>
        </a-breadcrumb>
    </div>
</template>
<script>
export default {
    name: 'hello',
    props: {
        list: {
            type: Array,
            default: []
        }
    },
    methods:{
        hanldeHistoryClick(route){
            if(route.route_path){
                this.$router.push({name: route.route_path})
            }
        }
    }
}
</script>

<style scoped lang="less">
.breadcrumb_item:hover{
    color: #1890ff;
    cursor: pointer;
}
</style>
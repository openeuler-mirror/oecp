<template>
  <ul>
    <li v-for="(page, index) in pageList" :key="index" :class="page.path == activePage ? 'act' : ''">
      <span @click="onTabClick(page.path)">{{page.title}}</span>
      <a-icon type="close" @click="onClose(page.path)"/>
    </li>
  </ul>
</template>

<script>
export default {
  name: 'tabs-header',
  props: {
    pageList: Array,
    activePage: String
  },
  methods: {
    onTabClick(key) {
      if(this.activePage !== key) {
        this.$emit('change', key)
      }
    },
    onClose(key) {
      this.$emit('close', key)
    }
  }
}
</script>

<style lang="less" scoped>
ul {
  display: flex;
  list-style-type: none;
  padding-left: 16px;
  margin-top: 16px;
  margin-bottom: 0px;
  li {
    padding: 5px 10px;
    background-color: rgb(250,250,250);
    margin-right: 10px;
    border-radius: 5px;
    cursor: pointer;
    span {
      font-size: 14px;
      margin-right: 10px;
    }
  }
  .act {
    background-color: #fff;
    color: rgb(24,144,255);
  }
}
</style>
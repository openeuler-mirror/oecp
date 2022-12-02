<template>
    <div class="mx-search-box-item">
        <span v-if="title" class="mx-search-box-item-label">{{title}}</span>
        <slot></slot>
    </div>
</template>
<script>
export default {
  name: 'mx_search_item',
  props: {
    title: {
        type: String,
        default: ''
    }
  },
  data () {
    return {
    }
  },
  methods: {
  }
}
</script>

<style>
.mx-search-box-item{
  display: inline-block;
  margin-right: 20px;
  line-height: 32px;
  position: relative;
}
.mx-search-box-item-label{
    margin: 0 8px 0 0;
    /* min-width: 65px; */
    text-align: right;
    display: inline-block;
}
.ant-select-selection__rendered{
  height: 32px !important;
}
</style>

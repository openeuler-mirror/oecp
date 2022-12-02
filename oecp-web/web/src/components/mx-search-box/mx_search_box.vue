<template>
    <div class="mx-search-con search-con-top" style="margin-bottom:0px;line-height:40px">
      <div class="div-search">
        <slot name="searchbox"></slot>
      </div>
      <div class="div-add">
        <slot name="actionbox"></slot>
      </div>
    </div>
</template>
<script>
export default {
  name: 'mx_search',
  components: {
  },
  props: {
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
.mx-search-con{
    position: relative;
  /* min-height: 50px; */
  padding-bottom: 24px;
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  flex-wrap: wrap;
  align-content: flex-start;
}
.div-add{
    display: flex;
    align-items: center;
    line-height: 0;
}
</style>


/* eslint-disable */
// lazy loading Components
// https://github.com/vuejs/vue-router/blob/dev/examples/lazy-loading/app.js#L8
// eslint-disable-next-line
export default (name) => () => import(`@/views//${name}`)

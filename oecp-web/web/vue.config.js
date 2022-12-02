
module.exports = {
  lintOnSave: false,
  // css 相关选项
  publicPath: process.env.NODE_ENV === 'production' ?
    process.env.VUE_APP_PUBLIC_PATH : '/',
  productionSourceMap:  process.env.NODE_ENV === 'production' ? false : true,
  chainWebpack: config => {
    const svgRule = config.module.rule('svg');
    svgRule.uses.clear();
    svgRule.use('vue-svg-loader').loader('vue-svg-loader');
  },
  css: {
    /*为预处理器 loader 传递自定义选项*/
    loaderOptions: {
      sass: {
        prependData: `@import "@/assets/css/index.css";`
      }
    }
  },

  devServer: {
    // port: 8082,
    proxy: {
      '`process.env.VUE_APP_PUBLIC_PATH`api/v1': {
        target: process.env.VUE_APP_API_BASE_URL, //上线的时候改成正常的ip地址
        changeOrigin: true,
        ws: true,
        pathRewrite: {
          '^`process.env.VUE_APP_PUBLIC_PATH`api/v1': process.env.VUE_APP_API_PREFIX,
        }
      },
      '/api/v1': {
        target: process.env.VUE_APP_API_BASE_URL, //上线的时候改成正常的ip地址
        changeOrigin: true,
        ws: true,
        pathRewrite: {
          '^/api/v1': process.env.VUE_APP_API_PREFIX,
        }
      }

    }
  },
  pages: {
    index: {
      // page 的入口
      entry: 'src/main.js',
      // 模板来源
      template: 'public/index.html',
      // 在 dist/index.html 的输出
      filename: 'index.html',
      // 当使用 title 选项时，
      // template 中的 title 标签需要是 <title><%= htmlWebpackPlugin.options.title %></title>
      title: 'OECP报告展示'
    }
  }
};
import axios from 'axios'
import { message } from "ant-design-vue"
// import { mapActions } from 'vuex'

class HttpRequest {
    constructor (baseUrl = baseURL) {
        this.baseUrl = baseUrl
        this.queue = {}
    }
    getInsideConfig () {
        const config = {
        baseURL: this.baseUrl,
        headers: {
            'Content-Type': 'application/json'
        }
        }
        return config
    }
    distroy (url) {
        delete this.queue[url]
        if (!Object.keys(this.queue).length) {
        }
    }
    interceptors (instance, url) {
        var self = this
        instance.interceptors.request.use(config => {
            if (!Object.keys(this.queue).length) {
            }
            this.queue[url] = true
            return config
        }, error => {
            return Promise.reject(error)
        })
        instance.interceptors.response.use(res => {
            // if(res.data && res.data.status.code != 0) {
            //     if(res.data.message) {
            //         message.error(res.data.message)
            //     }
            // }
            const { data, status } = res
            return { data, status }
        }, error => {
        console.log('error', error)
        if(error.message && !error.response) {
            message.error( "网络异常")
            return
        }
        this.distroy(url)
            return Promise.reject(error)
        })
    }
    request (options) {
        const instance = axios.create()
        options = Object.assign(this.getInsideConfig(), options)
        this.interceptors(instance, options.url)
        return instance(options)
    }
}
export default HttpRequest

import axios from '@/libs/api.request'
const baseUrl = process.env.VUE_APP_API_BASE_URL + process.env.VUE_APP_API_PREFIX
console.log('baseUrl', baseUrl)

const get = (url, url_data={}) => {
    // const baseUrl = urlConfig().mainApiUrl
    console.log(baseUrl)
    var _url = baseUrl + url
    return axios.request({
        url: _url,
        params: url_data,
        method: 'get'
    })
}

const post = (url, params) => {
    var _url = baseUrl + url
    axios.default
    return axios.request({
        url: _url,
        data: params,
        method: 'post'
    })
}

const del = (url, params) => {
    var _url = baseUrl + url
    return axios.request({
        url: _url,
        method: 'delete',
        data: params
    })
}

const upload = (url, data, progressCallback) => {
    var _url = baseUrl + url
    return axios.request({
        url: _url,
        method: 'post',
        data: data,
        onUploadProgress: function(progressEvent) {
            if (progressEvent.lengthComputable) {
                if(progressCallback){
                    progressCallback(progressEvent);
                }
            }
          },
    
    })
}

const uploadAsync = async (url, data, progressCallback) => {
    var _url = baseUrl + url
    return await axios.request({
        url: _url,
        async: true,
        method: 'post',
        data: data,
        onUploadProgress: function(progressEvent) {
            if (progressEvent.lengthComputable) {
                if(progressCallback){
                    progressCallback(progressEvent);
                }
            }
          },
    
    })
}




export default {
    get,
    post,
    del,
    upload,
    uploadAsync
}
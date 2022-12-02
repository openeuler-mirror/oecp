import HttpRequest from '@/libs/axios'
import config from '@/config'
const baseUrl = process.env.VUE_APP_API_BASE_URL
const axios = new HttpRequest(baseUrl)
export default axios

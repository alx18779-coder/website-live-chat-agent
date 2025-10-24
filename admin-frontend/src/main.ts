import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import naive from 'naive-ui'
import './style.css'
import App from './App.vue'

const app = createApp(App)

// 安装插件
app.use(createPinia())
app.use(router)
app.use(naive)

app.mount('#app')

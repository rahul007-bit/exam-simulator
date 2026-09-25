import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { initTheme } from './composables/useTheme'
import { initAppStores } from './stores'
import './assets/styles/tokens.css'
import './assets/styles/base.css'

initTheme()

const app = createApp(App)
const pinia = createPinia()

app.use(pinia).use(router).mount('#app')

// Hydrate the session/timer stores from the backend (non-blocking).
void initAppStores(pinia)

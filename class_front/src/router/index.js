import { createRouter, createWebHistory } from 'vue-router'

// 1. 基础页面导入
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import Profile from '../views/Profile.vue'
import Home from '../views/Home.vue' 

const routes = [
  { 
    path: '/', 
    redirect: '/login' 
  },
  { 
    path: '/login', 
    name: 'Login',
    component: Login 
  },
  { 
    path: '/register', 
    name: 'Register',
    component: Register 
  },
  { 
    path: '/dashboard', 
    component: Dashboard,
    redirect: '/dashboard/home', // 登录后默认进入看板首页
    children: [
      { 
        path: 'home', 
        name: 'Home',
        component: Home 
      }, 
      { 
        path: 'profile', 
        name: 'Profile',
        component: Profile 
      },
      
      // 💡 智慧巡课 - 实时画面 (对应 /dashboard/monitor)
      { 
        path: 'monitor', 
        name: 'Monitor',
        component: () => import('../views/Monitor.vue') 
      },
      
      // 💡 巡课记录管理 - 历史档案 (对应 /dashboard/history)
      { 
        path: 'history', 
        name: 'History',
        component: () => import('../views/History.vue') 
      }
    ] 
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 💡 导航守卫：防止未登录用户直接访问 dashboard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access') || localStorage.getItem('token')
  
  if (to.path.startsWith('/dashboard') && !token) {
    // 如果去后台页面但没 token，强制踢回登录页
    next('/login')
  } else {
    next()
  }
})

export default router
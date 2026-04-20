<template>
  <div class="common-layout">
    <el-container>
      <el-header class="nav-header">
        <div class="logo">智慧课堂巡课系统</div>
        
        <el-menu
          mode="horizontal"
          :ellipsis="false"
          :default-active="activeMenu" 
          class="top-menu"
          @select="handleSelect"
        >
          <el-menu-item index="home">系统首页</el-menu-item>
          
          <el-menu-item index="monitor" v-if="userGroup !== '游客'">实时巡课</el-menu-item>
          <el-menu-item index="history" v-if="userGroup !== '游客'">历史巡课</el-menu-item> 
          
          <el-menu-item index="profile">信息维护</el-menu-item>
          
          <div class="flex-grow" /> 
          <el-sub-menu index="user">
            <template #title>欢迎，{{ nickname }}</template>
            <el-menu-item index="logout">退出登录</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-header>

      <el-main class="main-content">
        <router-view></router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue' 
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios' 

const router = useRouter()
const route = useRoute()

// 1. 定义响应式身份变量
const localName = localStorage.getItem('username') || '用户'
const nickname = ref(localName) 
const userGroup = ref('游客') // 默认设为游客，增强安全性

// 计算属性：用于菜单高亮
const activeMenu = computed(() => {
  const path = route.path
  if (path.includes('home')) return 'home'
  if (path.includes('monitor')) return 'monitor'
  if (path.includes('history')) return 'history'
  if (path.includes('profile')) return 'profile'
  return 'home'
})

onMounted(async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    router.push('/login')
    return
  }

  try {
    const res = await axios.get('http://localhost:8000/api/user-info/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    // 💡 核心逻辑：优先显示真实姓名
    // 如果 real_name 有值就用它，否则用 username
    const displayName = res.data.real_name || res.data.username
    
    // 更新右上角显示的文字，格式为：姓名 (角色)
    nickname.value = `${displayName} (${res.data.group})`
    
    // 存储组名
    userGroup.value = res.data.group 
    
    // 更新本地缓存，确保其他页面也能拿到最新的账号名
    localStorage.setItem('username', res.data.username)

    // 💡 路由访问越权拦截
    if (userGroup.value === '游客' && (route.path.includes('history') || route.path.includes('monitor'))) {
       ElMessage.warning('您的权限不足以访问此功能')
       router.push('/dashboard/home')
    }

  } catch (err) {
    console.error('获取身份失败', err)
    if (err.response?.status === 401) {
      router.push('/login')
    }
  }
})

const handleSelect = (key) => {
  if (key === 'logout') {
    localStorage.clear()
    ElMessage.success('已安全退出')
    router.push('/login')
    return
  }
  router.push(`/dashboard/${key}`)
}
</script>

<style scoped>
.nav-header { padding: 0; display: flex; align-items: center; background-color: #fff; border-bottom: 1px solid #dcdfe6; }
.logo { width: 250px; padding-left: 20px; font-size: 18px; font-weight: bold; color: #409eff; }
.top-menu { flex: 1; border-bottom: none !important; }
.flex-grow { flex-grow: 1; }
.main-content {
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px); 
  padding: 0; /* 这里的 padding 建议设为 0，由子页面自己控制间距 */
}
</style>
<template>
  <div class="login-wrapper">
    <el-card class="login-box">
      <template #header>
        <h2 class="title">智慧课堂巡课系统 - 用户登录</h2>
      </template>

      <el-form :model="loginForm" label-width="60px">
        <el-form-item label="账号">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="请输入密码" 
            show-password 
          />
        </el-form-item>

        <div class="btn-group">
          <el-button type="primary" @click="handleLogin" :loading="loading">登录系统</el-button>
          <el-button @click="goToRegister">新用户注册</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus' // 引入漂亮的顶部弹窗
import { useRouter } from 'vue-router'

const loginForm = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  // 基础检查：别空着手去
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }

  try {
    // 2. 发送 POST 请求到 Django 的登录接口
    // 注意：这里的端口 8000 是你 Django 运行的地址
    const response = await axios.post('http://127.0.0.1:8000/api/login/', {
      username: loginForm.username,
      password: loginForm.password
    })

    // 3. 如果成功，Django 会返回一串 Token（通行证）
    const token = response.data.access
    localStorage.setItem('token', response.data.access)// 把通行证存在浏览器里，下次不用再登录
    localStorage.setItem('username', loginForm.username)

    ElMessage.success('登录成功！欢迎进入巡课系统')
    router.push('/dashboard')
    
    // 4. 这里暂时打印一下，证明我们拿到通行证了
    console.log('拿到的通行证是：', token)

  } catch (error) {
    // 5. 如果失败（密码错了、用户名不存在、或者 Django 没开）
    console.error(error)
    ElMessage.error('登录失败：用户名或密码错误，或后端未启动')
  }
}

// 3. 注册逻辑（暂时留空，你可以照着写一个 Register.vue）
const router = useRouter()

const goToRegister = () => {
  router.push('/register') // 点击后跳到 /register 网址
}
</script>

<style scoped>
/* 1. 全局背景：改为干净的浅灰色，不再用渐变 */
.login-wrapper {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5; /* 经典的后台背景色 */
}

/* 2. 登录卡片：去掉花哨的圆角，回归朴素 */
.login-box {
  width: 380px;
  border-radius: 4px; /* 很小的圆角，看起来更硬朗 */
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1); /* 淡淡的阴影，让卡片浮起来 */
  border: 1px solid #ebeef5;
}

/* 3. 卡片头部：改为白底蓝字 */
:deep(.el-card__header) {
  background-color: #fff;
  border-bottom: 1px solid #ebeef5;
  padding: 15px 20px;
}

.title {
  text-align: center;
  color: #409eff; /* 使用 Element Plus 标准蓝 */
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 1px; /* 字间距，看起来更专业 */
}

/* 4. 调整表单间距 */
:deep(.el-form-item) {
  margin-bottom: 22px;
}

/* 5. 调整标签文字颜色 */
:deep(.el-form-item__label) {
  color: #606266;
  font-weight: 500;
}

/* 6. 按钮组：让它们更整齐 */
.btn-group {
  text-align: center;
  padding-top: 10px;
}

/* 调整注册按钮的样式，让它不那么抢眼 */
.btn-group .el-button--default {
  color: #909399;
  border-color: #dcdfe6;
}

.btn-group .el-button--default:hover {
  color: #409eff;
  border-color: #c6e2ff;
  background-color: #ecf5ff;
}
</style>
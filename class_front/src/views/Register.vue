<template>
  <div class="register-wrapper">
    <el-card class="register-box">
      <template #header>
        <h2 class="title">新用户注册</h2>
      </template>

      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" show-password />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="email" placeholder="可选" />
        </el-form-item>

        <div class="btn-group">
          <el-button type="primary" @click="doRegister">提交注册</el-button>
          <el-button @click="goToLogin">返回登录</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const username = ref('')
const password = ref('')
const email = ref('')

// 注册动作
const doRegister = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/register/', {
      username: username.value,
      password: password.value,
      email: email.value
    })
    
    ElMessage.success('注册成功！请登录')
    router.push('/login') // 注册完自动跳回登录页面
  } catch (err) {
    ElMessage.error('注册失败，用户名可能重复了')
  }
}

// 返回登录动作
const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-wrapper { height: 100vh; display: flex; justify-content: center; align-items: center; background-color: #f0f2f5; }
.register-box { width: 400px; }
.title { text-align: center; color: #409eff; }
.btn-group { text-align: center; margin-top: 20px; }
</style>
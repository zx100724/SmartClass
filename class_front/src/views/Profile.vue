<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>个人信息维护</span>
        </div>
      </template>

      <div class="avatar-section">
        <div class="mock-avatar">{{ userInfo.real_name ? userInfo.real_name.charAt(0) : (userInfo.username.charAt(0).toUpperCase()) }}</div>
        <div class="role-badge"><el-tag type="success" size="small">{{ userGroup }}</el-tag></div>
      </div>

      <el-form :model="userInfo" label-width="100px" style="max-width: 460px; margin: 0 auto;">
        
        <el-form-item label="用户名">
          <el-input v-model="userInfo.username" disabled />
          <div class="form-tip">账号作为唯一标识，不可修改</div>
        </el-form-item>

        <el-form-item label="真实姓名" required>
          <el-input 
            v-model="userInfo.real_name" 
            placeholder="请输入真实姓名 (用于巡课记录显示)" 
            clearable
            maxlength="10"
          />
        </el-form-item>

        <el-form-item label="电子邮箱">
          <el-input v-model="userInfo.email" placeholder="请输入绑定的邮箱地址" clearable />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveProfile" :loading="saving" style="width: 100%;">
            保存个人资料
          </el-button>
        </el-form-item>

        <el-divider>安全设置：修改密码</el-divider>

        <el-form-item label="新密码">
          <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="输入新密码 (不修改请留空)" />
        </el-form-item>
        
        <el-form-item label="确认新密码">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次确认新密码" />
        </el-form-item>

        <el-form-item>
          <el-button type="danger" @click="handlePasswordChange" style="width: 100%;" plain>
            更新登录密码
          </el-button>
        </el-form-item>
        
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const saving = ref(false)
const userGroup = ref('加载中...')
const userInfo = reactive({ username: '', email: '', real_name: '' }) 
const passwordForm = reactive({ newPassword: '', confirmPassword: '' })

// 1. 获取个人信息
const fetchUserInfo = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return router.push('/login')
    const res = await axios.get('http://localhost:8000/api/user-info/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    userInfo.username = res.data.username
    userInfo.email = res.data.email
    userInfo.real_name = res.data.real_name || ''
    userGroup.value = res.data.group
  } catch (err) {
    ElMessage.error('身份验证失效或获取信息失败')
    if(err.response?.status === 401) router.push('/login')
  }
}

// 2. 保存资料修改 (包含姓名和邮箱)
const saveProfile = async () => {
  if (!userInfo.real_name.trim()) {
    ElMessage.warning('真实姓名不能为空！')
    return
  }

  saving.value = true
  try {
    const token = localStorage.getItem('token')
    await axios.post('http://localhost:8000/api/update-profile/', 
      { 
        email: userInfo.email,
        real_name: userInfo.real_name 
      }, 
      { headers: { 'Authorization': `Bearer ${token}` } }
    )
    ElMessage.success('个人资料更新成功')
    
    
  } catch (err) { 
    ElMessage.error(err.response?.data?.error || '资料更新失败') 
  } finally { 
    saving.value = false 
  }
}

const handlePasswordChange = async () => {
  if (!passwordForm.newPassword) {
    ElMessage.warning('新密码不能为空')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致！')
    return
  }
  try {
    const token = localStorage.getItem('token')
    await axios.post('http://localhost:8000/api/change-password/', {
      new_password: passwordForm.newPassword
    }, { headers: { 'Authorization': `Bearer ${token}` } })
    
    ElMessageBox.alert('密码修改成功，请使用新密码重新登录系统', '安全提示', {
      confirmButtonText: '去登录',
      type: 'success',
      callback: () => { 
        localStorage.clear()
        router.push('/login')
      }
    })
  } catch (err) { 
    ElMessage.error('修改密码失败，请检查网络或联系管理员') 
  }
}

onMounted(fetchUserInfo)
</script>

<style scoped>
.profile-container { 
  padding: 30px; 
  display: flex; 
  justify-content: center; 
  background-color: #f5f7fa; 
  min-height: calc(100vh - 60px); 
}
.profile-card { 
  width: 100%; 
  max-width: 650px; 
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.card-header { 
  font-weight: bold; 
  font-size: 16px;
  color: #303133; 
}

/* 💡 新增的头像样式 */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
}
.mock-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #409eff;
  color: white;
  font-size: 32px;
  font-weight: bold;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 15px;
  box-shadow: 0 4px 12px rgba(64,158,255,0.3);
  text-transform: uppercase;
}
.role-badge {
  margin-top: -5px;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
  margin-top: 5px;
}
</style>
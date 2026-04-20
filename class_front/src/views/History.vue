<template>
  <div class="history-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>历史巡课记录</span>
          <el-button type="primary" size="small" @click="fetchHistory" :loading="loading">
            刷新数据
          </el-button>
        </div>
      </template>

<div class="simple-search-bar">
        <div class="search-wrapper">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索课程名称 / 教师姓名 / 巡课员... " 
            class="global-search-input"
            @keyup.enter="handleSearch"
          />
          <button class="clear-btn" v-show="searchQuery" @click="resetSearch">✖</button>
        </div>
      </div>

      <el-table :data="tableData" style="width: 100%" v-loading="loading" stripe border>
        
        <el-table-column prop="created_at" label="巡课时间" width="150" align="center" />
        
        <el-table-column prop="course_name" label="课程名称" min-width="120" />
        
        <el-table-column prop="teacher_name" label="授课教师" min-width="100" />
        
        <el-table-column label="到课人数" width="100" align="center">
          <template #default="scope">
            <el-tag type="success">{{ scope.row.ai_attendance }} 人</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="AI专注度" width="90" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.ai_focus_rate > 80 ? 'success' : 'warning'">
              {{ scope.row.ai_focus_rate }}%
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="人工评分" width="170" align="center">
          <template #default="scope">
            <el-rate v-model="scope.row.score" disabled show-score text-color="#ff9900" />
          </template>
        </el-table-column>
        
        <el-table-column prop="tags" label="行为标签" min-width="150">
          <template #default="scope">
            <el-tag 
              v-for="(tag, index) in (scope.row.tags ? scope.row.tags.split(',') : [])" 
              :key="index" 
              size="small" 
              style="margin-right: 5px; margin-bottom: 5px;"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="inspector_name" label="巡课员" min-width="100" align="center" />
        
<el-table-column label="操作" width="90" align="center">
  <template #default="scope">
    <el-button 
      v-if="scope.row.inspector_username === currentUsername"
      type="danger" 
      size="small" 
      @click="handleDelete(scope.row.id)"
    >
      删除
    </el-button>
  </template>
</el-table-column>

      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const loading = ref(false)

// 当前登录的用户名，用于判断是否显示删除按钮
const currentUsername = ref(localStorage.getItem('username') || '')

// 搜索框双向绑定的值
const searchQuery = ref('')

// 获取历史记录列表 (带全局搜索参数)
const fetchHistory = async () => {
  loading.value = true
  const token = localStorage.getItem('token') 
  
  try {
    const res = await axios.get('http://localhost:8000/api/records/history/', {
      headers: { 'Authorization': `Bearer ${token}` },
      // 💡 只有这里有改动：将 keyword 发给后端
      params: { keyword: searchQuery.value.trim() } 
    })
    tableData.value = res.data.data
  } catch (err) {
    console.error(err)
    if (err.response?.status === 403) {
      ElMessage.error('权限不足，无法查看历史数据')
    } else if (err.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
    } else {
      ElMessage.error('无法加载历史数据，请检查网络')
    }
  } finally {
    loading.value = false
  }
}

// 触发搜索
const handleSearch = () => {
  fetchHistory()
}

// 重置搜索
const resetSearch = () => {
  searchQuery.value = ''
  fetchHistory()
}

// 删除某条记录
const handleDelete = (id) => {
  ElMessageBox.confirm(
    '此操作将永久删除该巡课记录, 是否继续?',
    '危险操作',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    const token = localStorage.getItem('token')
    try {
      await axios.delete(`http://localhost:8000/api/records/history/${id}/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      ElMessage.success('记录已成功删除')
      fetchHistory() // 刷新表格
    } catch (err) {
      console.error(err)
      const errorMsg = err.response?.data?.error || '删除失败，请检查网络或权限'
      ElMessage.error(errorMsg)
    }
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

// 页面加载时请求一次默认数据
onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.history-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

/* 🔍 搜索栏样式 */
.simple-search-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 25px;
  gap: 15px;
}

.search-wrapper {
  position: relative;
  width: 50%;
  max-width: 600px;
}

.global-search-input {
  width: 100%;
  padding: 10px 40px 10px 20px; /* 留出右侧叉号的空间 */
  border: 1px solid #dcdfe6;
  border-radius: 20px;
  outline: none;
  font-size: 14px;
  background: #f5f7fa;
  transition: all 0.3s;
}

.global-search-input:focus {
  border-color: #409eff;
  background: #fff;
  box-shadow: 0 0 8px rgba(64,158,255,0.2);
}

.clear-btn {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 14px;
  padding: 5px;
}

.clear-btn:hover {
  color: #f56c6c;
}
.search-wrapper {
  position: relative;
  width: 60%; /* 从 50% 加大到 60% */
  max-width: 700px;
}

</style>
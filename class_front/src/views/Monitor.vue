<template>
  <div class="monitor-container">
    <div class="tool-bar">
      <div class="status-bar">
        <span>当前共 <strong class="highlight-count">{{ onlineClassrooms.length }}</strong> 个课堂</span>
      </div>
      
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索课程名称 / 班级号 / 教师姓名..." 
          class="search-input"
        />
        <span class="clear-btn" v-show="searchQuery" @click="searchQuery = ''">✖</span>
      </div>
      
      <button class="refresh-btn" @click="fetchMonitorData">刷新画面</button>
    </div>

    <div class="video-grid" v-if="onlineClassrooms.length > 0">
<div class="video-card" v-for="room in onlineClassrooms" :key="room.id" @click="openRoomDetail(room)">
  <div class="card-header">
    <span class="room-name">{{ room.room_name || room.name }}</span>
    <span :class="['status-dot', (room.status || room.camera?.status) ? 'online' : 'offline']">
      {{ (room.status || room.camera?.status) ? '● 设备在线' : '● 设备离线' }}
    </span>
  </div>

  <div class="card-body">
    <template v-if="room.status || room.camera?.status">
      <video v-if="getVideoUrl(room)" :src="getVideoUrl(room)" autoplay loop muted class="mock-media"></video>
      <img v-else-if="getImageUrl(room)" :src="getImageUrl(room)" class="mock-media" alt="监控画面" />
      <div v-else class="no-signal">无信号</div>
    </template>
    <template v-else>
      <div class="no-signal offline-overlay">
        <span class="offline-icon">🔌</span>
        <span>设备已离线</span>
      </div>
    </template>
  </div>

  <div class="card-footer" v-if="room.current_course">
    <div class="course-info">
      <span class="icon"></span> {{ room.current_course.name }}
    </div>
    <div class="teacher-info">
      <span>{{ room.current_course.teacher }}</span>
      <span class="v-line">|</span>
      <span>{{ room.current_course.classes?.join(', ') || '暂无班级' }}</span>
    </div>
  </div>

  <div class="card-footer free-time" v-else>
    <div class="free-info">系统故障请联系工作人员</div>
  </div>
</div>
    </div>
    
    <div v-else class="empty-state">
      <div class="empty-icon"></div>
      <p v-if="searchQuery">未找到与 "{{ searchQuery }}" 相关的课堂</p>
      <p v-else>当前时间段全校无正在进行的课程</p>
    </div>

    <div class="modal-overlay" v-if="selectedRoom" @click.self="closeRoomDetail">
      <div class="modal-content">
        
        <div class="modal-header">
          <div class="modal-title">
            <span class="room-title">{{ selectedRoom.room_name || selectedRoom.name }}</span>
            <span :class="['status-badge', selectedRoom.status || selectedRoom.camera?.status ? 'online' : 'offline']">
              {{ selectedRoom.status || selectedRoom.camera?.status ? '🔴实时监控中' : '⚫ 设备已离线' }}
            </span>
          </div>
          <button class="close-btn" @click="closeRoomDetail">✖</button>
        </div>

        <div class="modal-main-layout">
          <div class="modal-left">
            <div class="modal-video-wrapper">
              <template v-if="selectedRoom.status || selectedRoom.camera?.status">
                <video v-if="getVideoUrl(selectedRoom)" :src="getVideoUrl(selectedRoom)" autoplay controls class="modal-media"></video>
                <img v-else-if="getImageUrl(selectedRoom)" :src="getImageUrl(selectedRoom)" class="modal-media" alt="监控画面" />
                <div v-else class="modal-no-signal">📡 获取不到视频流信号</div>
              </template>
              <template v-else>
                <div class="modal-no-signal offline">
                  <span class="offline-icon">🔌</span>
                  <span>当前设备处于离线状态</span>
                </div>
              </template>
            </div>
            
            <div class="modal-course-info" v-if="selectedRoom.current_course">
              <div class="info-tag">{{ selectedRoom.current_course.name }}</div>
              <div class="info-tag">{{ selectedRoom.current_course.teacher }}</div>
              <div class="info-tag">{{ selectedRoom.current_course.classes?.join(', ') || '暂无数据' }}</div>
            </div>
          </div>

<div class="modal-right">
            
            <template v-if="selectedRoom.status || selectedRoom.camera?.status">
              <div class="panel-tabs">
                <div :class="['p-tab', activePanel === 'attendance' ? 'active' : '']" @click="switchPanel('attendance')">考勤</div>
                <div :class="['p-tab', activePanel === 'ai' ? 'active' : '']" @click="switchPanel('ai')">AI分析</div>
                <div :class="['p-tab', activePanel === 'evaluate' ? 'active' : '']" @click="switchPanel('evaluate')">评价</div>
              </div>

              <div class="panel-content">
                
                <div v-if="activePanel === 'attendance'" class="panel-item attendance-panel">
                  <h3 class="panel-title">实时考勤计数</h3>
                  
                  <div v-if="attendanceLoading" class="ai-loading">
                    <div class="lds-ring"><div></div><div></div><div></div><div></div></div>
                    <p>正在抓拍并识别人数...</p>
                  </div>

                  <div v-else-if="attendanceData" class="fade-in">
                    <div class="attendance-ring">
                      <div class="ring-text">
                        <span class="rate" :style="{color: getAttendanceColor(attendanceData.ratio)}">{{ attendanceData.ratio }}%</span>
                        <span class="label">到课率</span>
                      </div>
                    </div>
                    <div class="attendance-stats">
                      <div class="stat"><span class="label">应到</span><span class="val">{{ attendanceData.total }}</span></div>
                      <div class="stat"><span class="label">实到</span><input type="number" v-model.number="attendanceData.actual" class="edit-input-mini"/></div>
                      <div class="stat"><span class="label">缺席</span><span class="val red">{{ attendanceData.absent }}</span></div>
                    </div>
                  </div>

                  <div v-else class="empty-state-small">
                    <p>请点击下方按钮开始分析</p>
                  </div>

                  <button class="action-btn" @click="triggerFacialAttendance" :disabled="attendanceLoading">
                    {{ attendanceLoading ? '识别中...' : '无感考勤' }}
                  </button>
                </div>

                <div v-if="activePanel === 'ai'" class="panel-item ai-panel">
                  <div class="panel-header-with-btn">
                    <h3 class="panel-title">课堂动态感知</h3>
                    <button class="small-refresh-btn" @click="triggerAiAnalysis" :disabled="aiLoading">
                      {{ aiLoading ? '扫描中...' : '重新感知' }}
                    </button>
                  </div>
                  
                  <div v-if="aiLoading" class="ai-loading">
                    <div class="scanner-bar"></div>
                    <p>调用 YOLO 模型推理中...</p>
                  </div>

                  <div v-else-if="aiData" class="ai-results fade-in">
                    <div class="ai-metric">
                      <div class="metric-header">
                        <span>专注度指数</span>
                        <span :class="['score', getFocusColorClass(aiData.focus_rate)]">
                          {{ aiData.focus_level }} ({{ aiData.focus_rate }}%)
                        </span>
                      </div>
                      <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: aiData.focus_rate + '%', background: getFocusBgColor(aiData.focus_rate) }"></div>
                      </div>
                    </div>

                    <div class="raw-data-tags">
                      <span v-for="(val, key) in aiData.raw_counts" :key="key" v-show="val > 0" class="mini-tag">
                        {{ formatActionName(key) }}: {{ val }}人
                      </span>
                    </div>

                    <div class="ai-warnings" v-if="aiData.warnings && aiData.warnings.length > 0">
                      <p class="list-title">🚨 异常行为检测：</p>
                      <div class="warning-item" v-for="(warn, idx) in aiData.warnings" :key="idx">
                        <span class="icon">{{ warn.icon }}</span> {{ warn.type }}: <strong>{{ warn.count }}</strong> 人
                      </div>
                    </div>
                    <div class="ai-warnings success" v-else>
                      <p class="list-title" style="color:#67c23a; margin-bottom:0;">✅ 课堂秩序良好</p>
                    </div>
                  </div>
                </div>

                <div v-if="activePanel === 'evaluate'" class="panel-item evaluate-panel">
                  <h3 class="panel-title">填写巡课评价</h3>
                  <div class="eval-form">
                    <label>纪律评分</label>
                    <div class="star-rating">
                      <span v-for="n in 5" :key="n" @click="evalForm.rating = n" :class="['star', n <= evalForm.rating ? 'active' : '']">★</span>
                    </div>
                    <div class="tags-container">
                      <span v-for="tag in availableTags" :key="tag" :class="['eval-tag', evalForm.tags.includes(tag) ? 'selected' : '']" @click="toggleTag(tag)">
                        {{ tag }}
                      </span>
                    </div>
                    <textarea v-model="evalForm.comment" rows="4" placeholder="写下巡课意见..."></textarea>
                    <button class="action-btn submit-btn" @click="submitEvaluation">提交巡课记录</button>
                  </div>
                </div>

              </div>
            </template>
            
            <div v-else class="offline-panel-right">
              <div class="offline-icon-large">🔌</div>
              <h3>设备暂无连接</h3>
              <p>无法获取实时画面，AI 分析与考勤功能已禁用</p>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const roomList = ref([])
const searchQuery = ref('')
const selectedRoom = ref(null)
const activePanel = ref('attendance')

// 响应式变量
const aiData = ref(null)
const aiLoading = ref(false)
const attendanceData = ref(null)
const attendanceLoading = ref(false)

const evalForm = reactive({ rating: 5, tags: [], comment: '' })
const availableTags = ['纪律良好', '互动积极', '教师迟到', '后排睡觉', '板书清晰', '玩手机较多']

const getVideoUrl = (room) => room.camera?.mock_video || room.video_url
const getImageUrl = (room) => room.camera?.mock_image

const getHeaders = () => {
  const token = localStorage.getItem('access') || localStorage.getItem('token') || localStorage.getItem('access_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

const onlineClassrooms = computed(() => {
  let filtered = roomList.value;
  if (searchQuery.value.trim()) {
    const keyword = searchQuery.value.trim().toLowerCase();
    filtered = filtered.filter(room => {
      if (!room.current_course) return false;
      const c = room.current_course;
      return (c.name?.toLowerCase().includes(keyword)) || 
             (c.teacher?.toLowerCase().includes(keyword)) || 
             (c.classes?.some(cls => cls.toLowerCase().includes(keyword)));
    });
  }
  return filtered;
});

const fetchMonitorData = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/monitor/list/', { headers: getHeaders() });
    roomList.value = response.data.data || response.data;
  } catch (error) {
    if (error.response?.status === 401) router.push('/login');
  }
}

// 考勤计数
const triggerFacialAttendance = async () => {
  if (!selectedRoom.value) return;
  attendanceLoading.value = true;
  try {
    const response = await axios.get(`http://localhost:8000/api/monitor/facial-attendance/${selectedRoom.value.id}/`);
    attendanceData.value = response.data.data;
  } catch (error) { console.error(error); } 
  finally { attendanceLoading.value = false; }
}

// AI分析
const triggerAiAnalysis = async () => {
  if (!selectedRoom.value) return;
  aiLoading.value = true;
  try {
    const response = await axios.get(`http://localhost:8000/api/monitor/ai-analyze/${selectedRoom.value.id}/`);
    aiData.value = response.data.data;
  } catch (error) { console.error(error); }
  finally { aiLoading.value = false; }
}

const switchPanel = (panelName) => {
  activePanel.value = panelName;
  if (panelName === 'ai' && !aiData.value) triggerAiAnalysis();
  if (panelName === 'attendance' && !attendanceData.value) triggerFacialAttendance();
}

const openRoomDetail = (room) => {
  selectedRoom.value = room;
  aiData.value = null;
  attendanceData.value = null;
  switchPanel('attendance');
}

const closeRoomDetail = () => { selectedRoom.value = null }
const toggleTag = (tag) => {
  const i = evalForm.tags.indexOf(tag);
  i === -1 ? evalForm.tags.push(tag) : evalForm.tags.splice(i, 1);
}
const submitEvaluation = async () => {
  if (!selectedRoom.value) {
    alert("未选择教室，无法提交");
    return;
  }

  // 1. 抓取最新复核后的实到人数 (确保是数字类型)
  // 如果 attendanceData.value 存在，取其 actual 属性；否则默认为 0
  const finalAttendance = Number(attendanceData.value?.actual) || 0;

  // 2. 构造 payload
  const payload = {
    room_id: selectedRoom.value.id,
    course_name: selectedRoom.value.current_course?.name || '未知课程',
    teacher_name: selectedRoom.value.current_course?.teacher || '未知教师',
    
    // 💡 关键：这里必须提交你复核后的这个变量
    attendance_count: finalAttendance, 
    
    focus_rate: Number(aiData.value?.focus_rate) || 0,
    rating: evalForm.rating,
    tags: evalForm.tags.join(','), // 建议将数组转为字符串，防止后端解析 JSON 数组报错
    comment: evalForm.comment
  };

  // 3. 调试打印：在控制台看看发出去的数据对不对
  console.log("📤 准备提交的 Payload:", payload);

  try {
    // 💡 确保 getHeaders() 能够返回正确的 Authorization
    const headers = getHeaders();
    console.log("🔑 当前请求头:", headers);

    await axios.post('http://localhost:8000/api/records/manage/', payload, {
      headers: headers
    });
    
    alert('✅ 巡课记录已人工复核并存入系统！');
    
    // 提交成功后重置表单
    evalForm.rating = 5;
    evalForm.tags = [];
    evalForm.comment = '';
    closeRoomDetail();
    
  } catch (error) {
    // 💡 这里的打印非常重要，能看到后端具体的报错字段
    console.error("❌ 提交失败详细信息:", error.response?.data);
    const errorMsg = error.response?.data?.error || '服务器拒绝请求(400)';
    alert(`保存失败：${errorMsg}`);
  }
};

const getFocusColorClass = (r) => r >= 80 ? 'green' : r >= 60 ? 'orange' : 'red';
const getFocusBgColor = (r) => r >= 80 ? '#67c23a' : r >= 60 ? '#e6a23c' : '#f56c6c';
const getAttendanceColor = (r) => r >= 90 ? '#67c23a' : r >= 80 ? '#e6a23c' : '#f56c6c';
const formatActionName = (n) => ({ 'Listening': '听讲', 'Reading': '阅读', 'Writing': '书写', 'Turning around': '转头', 'Raising hand': '举手', 'Standing': '站立', 'Discussing': '讨论', 'Guiding': '教师指导' }[n] || n);

onMounted(() => fetchMonitorData());
</script>

<style scoped>
/* 基础布局 */
.monitor-container { padding: 20px; background-color: #f0f2f5; min-height: 100vh; font-family: sans-serif; }
.tool-bar { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 16px 24px; border-radius: 8px; margin-bottom: 24px; }
.highlight-count { color: #409eff; font-size: 1.4rem; }
.search-box { flex: 1; max-width: 400px; position: relative; margin: 0 20px; }
.search-input { width: 100%; padding: 10px 15px; border: 1px solid #dcdfe6; border-radius: 20px; outline: none; background: #f5f7fa; }
.refresh-btn { padding: 10px 20px; background: #409eff; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }

/* 视频格子 */
.video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 24px; }
.video-card { background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); cursor: pointer; transition: 0.3s; }
.video-card:hover { transform: translateY(-5px); }
.card-header { padding: 12px 15px; background: #2b2f3a; color: #fff; display: flex; justify-content: space-between; }
.status-dot { font-size: 0.8rem; padding: 2px 8px; border-radius: 12px; border: 1px solid; }
.status-dot.online { color: #67c23a; border-color: #67c23a; }
.card-body { height: 220px; background: #000; display: flex; align-items: center; justify-content: center; }
.mock-media { width: 100%; height: 100%; object-fit: cover; }
.card-footer { padding: 15px; background: #fff; }
.course-info { font-weight: bold; font-size: 1.1rem; margin-bottom: 5px; }

/* 弹窗样式 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
.modal-content { 
  width: 95%;          /* 💡 宽度占屏幕的 95% */
  max-width: 1600px;   /* 💡 最大宽度放宽到 1600px */
  height: 90vh;        /* 💡 新增：让整个黑框高度占屏幕的 90% */
  background: #1e1e1e; 
  border-radius: 12px; 
  display: flex; 
  flex-direction: column; 
  overflow: hidden; 
}
.modal-header { padding: 15px 20px; background: #141414; display: flex; justify-content: space-between; color: #fff; }
.modal-main-layout { 
  display: flex; 
  flex: 1;             /* 💡 核心：让内容区域自动填满弹窗剩下的所有高度 */
  /* height: 60vh; 删除这行固定高度！ */
}
.modal-left { flex: 7; background: #000; display: flex; flex-direction: column; }
.modal-video-wrapper { flex: 1; display: flex; align-items: center; justify-content: center; }
.modal-media { width: 100%; height: 100%; object-fit: contain; }
.modal-course-info { padding: 10px; display: flex; gap: 10px; background: #141414; }
.info-tag { padding: 5px 10px; background: #333; color: #409eff; border-radius: 4px; font-size: 0.9rem; }

.modal-right { flex: 3; background: #252526; display: flex; flex-direction: column; border-left: 1px solid #333; }
.panel-tabs { display: flex; border-bottom: 1px solid #333; }
.p-tab { flex: 1; padding: 15px; text-align: center; color: #909399; cursor: pointer; }
.p-tab.active { color: #409eff; border-bottom: 2px solid #409eff; background: #2d2d2d; }
.panel-content { flex: 1; padding: 20px; overflow-y: auto; color: #ccc; }

/* AI/考勤 内部组件 */
.panel-title { border-left: 4px solid #409eff; padding-left: 10px; margin-bottom: 20px; color: #fff; }
.attendance-ring { text-align: center; margin: 20px 0; }
.rate { font-size: 2.5rem; font-weight: bold; display: block; }
.attendance-stats { display: flex; justify-content: space-around; background: #141414; padding: 15px; border-radius: 8px; }
.stat { display: flex; flex-direction: column; align-items: center; }
.green { color: #67c23a; }
.red { color: #f56c6c; }

.ai-loading { text-align: center; padding: 40px 0; color: #409eff; }
.scanner-bar { width: 100%; height: 4px; background: #333; position: relative; overflow: hidden; margin-bottom: 10px;}
.scanner-bar::after { content:''; position: absolute; width:40%; height:100%; background:#409eff; animation: scan 1.5s infinite; }
@keyframes scan { 0%{left:-40%} 100%{left:100%} }

.ai-metric { margin-bottom: 20px; }
.progress-bar { height: 8px; background: #333; border-radius: 4px; overflow: hidden; margin-top: 5px;}
.progress-fill { height: 100%; transition: 0.5s; }
.raw-data-tags { display: flex; flex-wrap: wrap; gap: 5px; margin: 15px 0; }
.mini-tag { font-size: 0.8rem; background: #333; padding: 2px 6px; border-radius: 3px; }

.action-btn { width: 100%; padding: 12px; margin-top: 20px; background: #409eff; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
.star-rating { font-size: 1.5rem; color: #444; margin: 10px 0; }
.star.active { color: #e6a23c; }
.tags-container { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 15px; }
.eval-tag { padding: 4px 8px; background: #333; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
.eval-tag.selected { background: #409eff; color: #fff; }
textarea { width: 100%; background: #141414; border: 1px solid #333; color: #fff; padding: 10px; border-radius: 4px; outline: none; }

/* 考勤加载圆圈 */
.lds-ring { display: inline-block; width: 40px; height: 40px; border: 4px solid #67c23a; border-radius: 50%; border-top-color: transparent; animation: spin 1s infinite linear; }
@keyframes spin { to { transform: rotate(360deg); } }

.fade-in { animation: fadeIn 0.4s; }
@keyframes fadeIn { from{opacity:0} to{opacity:1} }

/* 离线状态右侧面板样式 */
.offline-panel-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  text-align: center;
  padding: 20px;
}
.offline-panel-right .offline-icon-large {
  font-size: 3rem;
  margin-bottom: 15px;
  opacity: 0.5;
}
.offline-panel-right h3 {
  color: #fff;
  margin-bottom: 10px;
  font-weight: normal;
}
.offline-panel-right p {
  font-size: 0.9rem;
  line-height: 1.5;
}


</style>
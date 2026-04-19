<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="title-bg">智慧课堂巡课系统实时看板</div>
    </div>

    <el-row :gutter="20" class="metric-row">
      <el-col :span="6">
        <div class="data-box">
          <div class="label">今日累计巡课次数</div>
          <div class="value">{{ stats.today_count || 0 }} <small>次</small></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="data-box blue">
          <div class="label">全校平均专注度</div>
          <div class="value">{{ stats.avg_focus || 0 }} <small>%</small></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="data-box green">
          <div class="label">今日到课总人数</div>
          <div class="value">{{ stats.total_student || 0 }} <small>人</small></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="data-box">
          <div class="label">当前系统时间</div>
          <div class="value time-font">{{ currentTime }}</div>
          <div class="date-footer">{{ currentDateStr }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="8">
        <div class="chart-wrapper">
          <div class="chart-title">巡课评价分数分布</div>
          <div id="scorePie" class="echart-box"></div>
        </div>
      </el-col>
      <el-col :span="16">
        <div class="chart-wrapper">
          <div class="chart-title">课堂专注度时段波动</div>
          <div id="focusLine" class="echart-box"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

const stats = ref({ today_count: 0, avg_focus: 0, total_student: 0 })
const currentTime = ref('')
const currentDateStr = ref('')
let timer = null
let pieChart = null
let lineChart = null

// 更新时间逻辑
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toTimeString().split(' ')[0]
  const y = now.getFullYear()
  const m = now.getMonth() + 1
  const d = now.getDate()
  currentDateStr.value = `${y}/${m}/${d}`
}


const initCharts = (data) => {
  // 饼图
  const pieDom = document.getElementById('scorePie')
  if (pieDom) {
    if (pieChart) pieChart.dispose() 
    pieChart = echarts.init(pieDom)
    pieChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: data && data.pie_data && data.pie_data.length > 0 
              ? data.pie_data 
              : [{ value: 0, name: '暂无数据' }],
        label: { color: '#8b949e' }
      }]
    })
  }

  // 初始化折线图
  const lineDom = document.getElementById('focusLine')
  if (lineDom) {
    if (lineChart) lineChart.dispose()
    lineChart = echarts.init(lineDom)
    lineChart.setOption({
      xAxis: { 
        type: 'category', 
        data: ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00'], 
        axisLabel: { color: '#8b949e' } 
      },
      yAxis: { 
        type: 'value', 
        max: 100,
        axisLabel: { color: '#8b949e' }, 
        splitLine: { lineStyle: { color: '#30363d' } } 
      },
      series: [{
        data: data && data.line_data ? data.line_data : [0, 0, 0, 0, 0, 0],
        type: 'line',
        smooth: true,
        symbol: 'circle',
        lineStyle: { color: '#58a6ff', width: 3 },
        areaStyle: { 
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(88, 166, 255, 0.3)' },
            { offset: 1, color: 'transparent' }
          ]) 
        }
      }]
    })
  }
}

// 获取数据并刷新看板
const fetchData = async () => {
  try {
    const res = await axios.get('http://192.168.226.117:8000/api/records/dashboard/')
    stats.value = res.data.metrics
    await nextTick()
    initCharts(res.data)
  } catch (e) {
    console.error("看板数据加载失败", e)
    initCharts(null)
  }
}

onMounted(async () => {
  updateTime()
  timer = setInterval(updateTime, 1000)

  await fetchData()

  const refreshTimer = setInterval(fetchData, 30000)
  onUnmounted(() => clearInterval(refreshTimer))

  window.addEventListener('resize', () => {
    pieChart?.resize(); lineChart?.resize();
  })
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  pieChart?.dispose(); lineChart?.dispose();
})
</script>

<style scoped>
.dashboard-container {
  background: #0a0c10;
  min-height: 100vh;
  padding: 25px;
  color: #fff;
}
.dashboard-header {
  text-align: center;
  margin-bottom: 30px;
  background: linear-gradient(to right, transparent, #1a3c7e, transparent);
  padding: 10px;
}
.title-bg { font-size: 26px; font-weight: bold; color: #00d2ff; letter-spacing: 2px; }

.data-box {
  background: #161b22;
  border: 1px solid #30363d;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  height: 130px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.label { color: #8b949e; font-size: 14px; margin-bottom: 8px; }
.value { font-size: 32px; font-weight: bold; }
.blue .value { color: #58a6ff; }
.green .value { color: #3fb950; }
.time-font { font-family: monospace; color: #58a6ff; }
.date-footer { color: #586069; font-size: 12px; margin-top: 5px; }

.chart-wrapper {
  background: #161b22;
  border: 1px solid #30363d;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}
.chart-title { margin-bottom: 15px; color: #c9d1d9; font-size: 14px; border-left: 4px solid #58a6ff; padding-left: 10px; }
.echart-box { height: 320px; width: 100%; }
</style>
<template>
  <div class="home-page">
    <!-- 欢迎横幅 -->
    <div class="home-hero">
      <div class="hero-glow glow-1"></div>
      <div class="hero-glow glow-2"></div>
      <span class="hero-label"><el-icon><Monitor /></el-icon>业务工作台</span>
      <h3>欢迎回来，{{ user?.name || user?.username }}</h3>
      <p class="hero-sub">今天是 {{ todayText }} · 合同、回款、发票和生产计划数据已实时汇总</p>
      <div class="hero-actions">
        <el-button type="primary" @click="router.push('/contract')" class="btn-cyber">
          <el-icon><Document /></el-icon>&nbsp;合同管理
        </el-button>
        <el-button type="primary" @click="router.push('/collection')" class="btn-cyber">
          <el-icon><Money /></el-icon>&nbsp;回款登记
        </el-button>
        <el-button class="btn-outline" @click="router.push('/plan')">
          <el-icon><Calendar /></el-icon>&nbsp;生产计划
        </el-button>
      </div>
    </div>

    <!-- 指标卡片 -->
    <div class="metric-grid">
      <div class="home-card" v-for="(item, i) in metricCards" :key="i" :class="'color-' + i">
        <div class="card-accent"></div>
        <div class="card-body">
          <div class="metric-label">
            <el-icon :class="'icon-' + i"><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </div>
          <div class="metric-value">{{ item.formatted }}</div>
          <div class="metric-note">{{ item.note }}</div>
        </div>
      </div>
    </div>

    <!-- 图表 -->
    <div class="charts-row">
      <div class="panel">
        <div class="panel-heading">
          <el-icon><TrendCharts /></el-icon>
          <span>企业年度业绩</span>
          <span class="panel-hint">2013–{{ charts.year_labels.at(-1) }}</span>
        </div>
        <div class="panel-body">
          <BaseChart :option="yearChartOption" height="300px" />
        </div>
      </div>
      <div class="panel">
        <div class="panel-heading">
          <el-icon><PieChart /></el-icon>
          <span>客户销售占比</span>
          <span class="panel-hint">本年度 TOP5</span>
        </div>
        <div class="panel-body">
          <BaseChart :option="pieChartOption" height="300px" />
        </div>
      </div>
    </div>

    <!-- 常用功能 -->
    <div class="section-title">
      <h4><el-icon><Grid /></el-icon>常用功能</h4>
    </div>
    <div class="quick-grid">
      <a class="quick-card" v-for="menu in quickMenus" :key="menu.title" :href="menu.url">
        <span class="quick-icon"><el-icon><component :is="menu.icon" /></el-icon></span>
        <span class="quick-name">{{ menu.title }}</span>
      </a>
    </div>

    <!-- 数据列表：最新合同 / 最新回款 / 最新发票 / 最新生产计划 / 最新售后 / 最新维修 / 最新返件 -->
    <div class="home-lists">
      <div class="panel home-table">
        <div class="panel-heading"><el-icon><Document /></el-icon><span>最新合同</span><router-link to="/contract" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-contract">合同号</th><th class="col-customer">客户</th><th>业务员</th><th class="col-date">日期</th><th class="col-amount text-right">金额</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentContracts" :key="row.id">
              <td class="col-index">{{ i + 1 }}</td>
              <td><router-link :to="`/contract/${row.id}`">{{ row.contract_number }}</router-link></td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td>{{ row.saler_name }}</td>
              <td>{{ row.date }}</td>
              <td class="text-right amount-cell">{{ fmt(row.total_price) }}</td>
            </tr>
            <tr v-if="!recentContracts.length"><td colspan="6" class="empty">暂无合同数据</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table">
        <div class="panel-heading"><el-icon><Money /></el-icon><span>最新回款</span><router-link to="/collection" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-contract">合同</th><th class="col-date">日期</th><th class="col-amount text-right">金额</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentCollections" :key="row.id">
              <td class="col-index">{{ i + 1 }}</td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td><router-link :to="`/contract/${row.contract_id}`">{{ row.contract_number }}</router-link></td>
              <td>{{ row.date }}</td>
              <td class="text-right amount-cell">{{ fmt(row.amount) }}</td>
            </tr>
            <tr v-if="!recentCollections.length"><td colspan="5" class="empty">暂无回款数据</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table">
        <div class="panel-heading"><el-icon><List /></el-icon><span>最新发票</span><router-link to="/invoice" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-contract">合同</th><th class="col-date">日期</th><th class="col-amount text-right">金额</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentInvoices" :key="row.id">
              <td class="col-index">{{ i + 1 }}</td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td><router-link :to="`/contract/${row.contract_id}`">{{ row.contract_number }}</router-link></td>
              <td>{{ row.date }}</td>
              <td class="text-right amount-cell">{{ fmt(row.amount) }}</td>
            </tr>
            <tr v-if="!recentInvoices.length"><td colspan="5" class="empty">暂无发票数据</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table">
        <div class="panel-heading"><el-icon><Calendar /></el-icon><span>最新生产计划</span><router-link to="/plan" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-contract">合同</th><th class="col-code">产品</th><th class="col-code">型号</th><th class="col-date">交货日期</th><th class="col-status">状态</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in upcomingPlans" :key="row.id">
              <td class="col-index">{{ i + 1 }}</td>
              <td><router-link :to="`/contract/${row.contract_id}`">{{ row.contract_number }}</router-link></td>
              <td>{{ row.productcategory_name }}</td>
              <td :title="row.product_model">{{ row.product_model }}</td>
              <td>{{ row.delivery_date }}</td>
              <td><span class="status-pill" :class="statusClass(row.completed_status)">{{ row.completed_status_display }}</span></td>
            </tr>
            <tr v-if="!upcomingPlans.length"><td colspan="6" class="empty">暂无生产计划</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table">
        <div class="panel-heading"><el-icon><PhoneFilled /></el-icon><span>最新售后服务</span><router-link to="/service" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-code">维修编号</th><th class="col-code">型号</th><th class="col-date">接收日期</th><th class="col-status">状态</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentServices" :key="row.id">
              <td class="col-index">{{ i + 1 }}</td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td><router-link :to="`/service`">{{ row.service_number }}</router-link></td>
              <td :title="row.product_model">{{ row.product_model }}</td>
              <td>{{ row.date }}</td>
              <td><span class="status-pill" :class="warrantyClass(row.warranty_end)">{{ row.warranty_end_display }}</span></td>
            </tr>
            <tr v-if="!recentServices.length"><td colspan="6" class="empty">暂无售后服务数据</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table">
        <div class="panel-heading"><el-icon><Setting /></el-icon><span>最新维修记录</span><router-link to="/servicedetail" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-code">维修编号</th><th class="col-code">型号</th><th>维修人</th><th class="col-date">完成时间</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentServiceDetails" :key="row.id">
              <td class="col-index">{{ i + 1 }}</td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td><router-link :to="`/servicedetail`">{{ row.service_number }}</router-link></td>
              <td :title="row.product_model">{{ row.product_model }}</td>
              <td>{{ row.repairman_name }}</td>
              <td>{{ row.repair_date }}</td>
            </tr>
            <tr v-if="!recentServiceDetails.length"><td colspan="6" class="empty">暂无维修记录</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table">
        <div class="panel-heading"><el-icon><RefreshLeft /></el-icon><span>最新售后返件</span><router-link to="/return-product" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-code">维修编号</th><th>发货人</th><th class="col-date">发货时间</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentReturnProducts" :key="row.id">
              <td class="col-index">{{ i + 1 }}</td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td><router-link :to="`/return-product`">{{ row.service_number }}</router-link></td>
              <td>{{ row.user_name }}</td>
              <td>{{ row.date }}</td>
            </tr>
            <tr v-if="!recentReturnProducts.length"><td colspan="5" class="empty">暂无售后返件数据</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import request from '../api/request'
import BaseChart from '../components/BaseChart.vue'
import {
  Monitor, Document, Money, Calendar, Briefcase, TrendCharts, List, User,
  PieChart, Grid, PhoneFilled, Tools, RefreshLeft, Setting,
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const user = computed(() => userStore.user)

const todayText = ref('')
const metrics = ref({})
const recentContracts = ref([])
const upcomingPlans = ref([])
const recentCollections = ref([])
const recentInvoices = ref([])
const recentServices = ref([])
const recentServiceDetails = ref([])
const recentReturnProducts = ref([])
const charts = ref({ year_labels: [], year_values: [], pie_labels: [], pie_values: [] })

const quickMenus = [
  { title: '合同管理', url: '/contract', icon: Document },
  { title: '回款登记', url: '/collection', icon: Money },
  { title: '发票登记', url: '/invoice', icon: List },
  { title: '生产计划', url: '/plan', icon: Calendar },
  { title: '客户管理', url: '/customer', icon: User },
  { title: '应收应付', url: '/chart', icon: TrendCharts },
  { title: '售后服务', url: '/service', icon: Tools },
  { title: '维修服务', url: '/servicedetail', icon: Setting },
]

const fmt = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const metricCards = computed(() => [
  { label: '本年度合同', formatted: '¥' + fmt(metrics.value.year_contract_amount), note: metrics.value.year_contract_count + ' 份', icon: Document, color: 0 },
  { label: '本季度回款', formatted: '¥' + fmt(metrics.value.quarter_collection_amount), note: metrics.value.quarter_collection_count + ' 笔记录', icon: TrendCharts, color: 1 },
  { label: '本月发票', formatted: '¥' + fmt(metrics.value.month_invoice_amount), note: metrics.value.month_invoice_count + ' 张登记', icon: List, color: 2 },
  { label: '待完工计划', formatted: metrics.value.pending_plans + ' 条', note: '', icon: Calendar, color: 3 },
  { label: '本月发货', formatted: metrics.value.month_delivery_qty + ' 件', note: metrics.value.month_delivery_count + ' 笔发货', icon: Money, color: 4 },
])

const statusClass = (val) => val === 2 ? 'warning' : val === 3 ? 'success' : ''
const warrantyClass = (val) => val === 1 ? 'danger' : val === 2 ? 'warning' : 'success'

const yearChartOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 18, right: 18, top: 34, bottom: 28, containLabel: true },
  xAxis: {
    type: 'category', data: charts.value.year_labels,
    axisLine: { lineStyle: { color: 'rgba(14,165,233,0.2)' } },
    axisLabel: { color: '#475569', fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#475569', fontSize: 11 },
    splitLine: { lineStyle: { color: 'rgba(14,165,233,0.06)' } },
  },
  series: [{
    name: '合同金额', type: 'bar', data: charts.value.year_values, barMaxWidth: 48,
    itemStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: '#60a5fa' }, { offset: 0.5, color: '#3b82f6' }, { offset: 1, color: '#1d4ed8' }] },
      borderRadius: [4, 4, 0, 0],
    },
  }],
}))

const pieChartOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: ¥{c}' },
  legend: {
    bottom: 0, type: 'scroll', orient: 'horizontal',
    textStyle: { color: '#475569', fontSize: 11 },
    itemWidth: 12, itemHeight: 8, pageIconSize: 8,
  },
  series: [{
    name: '销售业绩', type: 'pie', radius: ['38%', '64%'], center: ['50%', '44%'],
    avoidLabelOverlap: true, label: { color: '#475569', fontSize: 11 },
    data: charts.value.pie_labels.map((name, i) => ({ name, value: charts.value.pie_values[i] })),
    itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
    color: ['#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8', '#1e40af'],
    emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(14,165,233,0.25)' } },
  }],
}))

const load = async () => {
  try {
    const data = await request.get('/home/')
    todayText.value = data.today
    metrics.value = data.metrics || {}
    recentContracts.value = data.recent_contracts || []
    upcomingPlans.value = data.upcoming_plans || []
    recentCollections.value = data.recent_collections || []
    recentInvoices.value = data.recent_invoices || []
    recentServices.value = data.recent_services || []
    recentServiceDetails.value = data.recent_servicedetails || []
    recentReturnProducts.value = data.recent_return_products || []
    charts.value = data.charts || {}
  } catch (e) {}
}

onMounted(load)
</script>

<style scoped>
.home-page { animation: fadeIn .35s ease; }
@keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:none} }

/* ── Hero ── */
.home-hero {
  position: relative; overflow: hidden; border-radius: 14px;
  padding: 28px 32px; margin-bottom: 20px;
  background: linear-gradient(135deg, #e0f2fe 0%, #7dd3fc 50%, #38bdf8 100%);
  border: 1px solid rgba(56,189,248,0.35);
  box-shadow: 0 8px 32px rgba(56,189,248,0.15), inset 0 1px 0 rgba(255,255,255,0.5);
}
.hero-glow { position: absolute; border-radius: 50%; pointer-events: none; }
.glow-1 { top: -60px; right: -40px; width: 260px; height: 260px; background: radial-gradient(circle, rgba(255,255,255,0.25) 0%, transparent 70%); }
.glow-2 { bottom: -80px; left: 30%; width: 200px; height: 200px; background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%); }
.hero-label {
  display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px;
  border-radius: 999px; background: rgba(255,255,255,0.35); border: 1px solid rgba(255,255,255,0.5);
  color: #0369a1; font-size: 12px; font-weight: 600; letter-spacing: 1px;
}
.home-hero h3 { margin: 14px 0 6px; color: #0c4a6e; font-size: 26px; font-weight: 700; }
.hero-sub { margin: 0; color: #0284c7; font-size: 13px; }
.hero-actions { margin-top: 18px; display: flex; gap: 8px; }
.btn-cyber {
  background: linear-gradient(135deg, #38bdf8, #0284c7) !important;
  border: none !important; color: #fff !important;
  box-shadow: 0 4px 16px rgba(2,132,199,0.3) !important;
}
.btn-outline {
  background: rgba(255,255,255,0.4) !important; border: 1px solid rgba(2,132,199,0.35) !important;
  color: #0369a1 !important;
}
.btn-outline:hover { background: rgba(255,255,255,0.7) !important; border-color: #0284c7 !important; }

/* ── 指标卡片 ── */
.metric-grid { display: grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap: 14px; margin-bottom: 20px; }
.home-card {
  position: relative; border-radius: 12px; padding: 16px 18px;
  background: #fff; border: 1px solid var(--border);
  box-shadow: 0 2px 8px rgba(14,165,233,0.06), 0 4px 16px rgba(14,165,233,0.03);
  transition: transform .18s, box-shadow .18s; overflow: hidden;
}
.home-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(14,165,233,0.1); }
.card-accent { position: absolute; top: 0; left: 0; right: 0; height: 2px; }
.color-0 .card-accent { background: linear-gradient(90deg, #38bdf8, transparent); }
.color-1 .card-accent { background: linear-gradient(90deg, #0ea5e9, transparent); }
.color-2 .card-accent { background: linear-gradient(90deg, #8b5cf6, transparent); }
.color-3 .card-accent { background: linear-gradient(90deg, #f59e0b, transparent); }
.color-4 .card-accent { background: linear-gradient(90deg, #ef4444, transparent); }
.color-5 .card-accent { background: linear-gradient(90deg, #60a5fa, transparent); }
.card-body { position: relative; z-index: 1; }
.metric-label { display: flex; align-items: center; gap: 6px; color: #475569; font-size: 12px; font-weight: 600; letter-spacing: .5px; }
.metric-label .el-icon { font-size: 14px; }
.color-0 .metric-label .el-icon { color: #38bdf8; }
.color-1 .metric-label .el-icon { color: #0ea5e9; }
.color-2 .metric-label .el-icon { color: #8b5cf6; }
.color-3 .metric-label .el-icon { color: #f59e0b; }
.color-4 .metric-label .el-icon { color: #ef4444; }
.color-5 .metric-label .el-icon { color: #3b82f6; }
.metric-value { margin-top: 10px; font-size: 26px; font-weight: 700; color: #0c4a6e; line-height: 1.1; letter-spacing: -0.5px; }
.metric-note { margin-top: 5px; color: #94a3b8; font-size: 11px; }

/* ── 图表行 ── */
.charts-row { display: flex; gap: 16px; margin-bottom: 20px; }
.panel {
  flex: 1; border-radius: 12px; background: #fff;
  border: 1px solid var(--border);
  box-shadow: 0 2px 8px rgba(14,165,233,0.06); overflow: hidden;
}
.panel-heading {
  display: flex; align-items: center; gap: 8px; padding: 14px 18px;
  border-bottom: 1px solid var(--border); color: var(--text-main); font-size: 14px; font-weight: 600;
}
.panel-heading .el-icon { color: #38bdf8; }
.panel-hint { margin-left: auto; color: #94a3b8; font-size: 11px; font-weight: 400; }
.panel-body { padding: 12px; }

/* ── 常用功能 ── */
.section-title { display: flex; align-items: center; justify-content: space-between; margin: 22px 0 12px; }
.section-title h4 { display: flex; align-items: center; gap: 7px; margin: 0; color: var(--text-main); font-size: 15px; font-weight: 600; }
.section-title h4 .el-icon { color: #38bdf8; }
.see-all { color: #0ea5e9; font-size: 12px; text-decoration: none; font-weight: 500; }
.see-all:hover { text-decoration: underline; }

.quick-grid { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.quick-card {
  display: flex; align-items: center; padding: 12px 20px;
  border: 1px solid var(--border); border-radius: 10px; background: #fff;
  color: var(--text-main); text-decoration: none; font-size: 13px; font-weight: 500;
  transition: all .2s; gap: 8px;
}
.quick-card:hover { border-color: rgba(56,189,248,0.4); background: var(--blue-50); transform: translateY(-1px); box-shadow: 0 4px 16px rgba(14,165,233,0.1); }
.quick-icon {
  width: 32px; height: 32px; border-radius: 8px; background: var(--blue-100);
  display: flex; align-items: center; justify-content: center; color: #0ea5e9;
  transition: all .2s;
}
.quick-card:hover .quick-icon { background: #0ea5e9; color: #fff; }

/* ── 表格 ── */
.two-col { display: flex; gap: 16px; margin-bottom: 16px; }
.home-lists { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 16px; margin-bottom: 16px; }
.home-table { border-radius: 12px; background: #fff; border: 1px solid var(--border); overflow: hidden; }
.home-table .table { table-layout: fixed; width: 100%; border-collapse: collapse; margin-bottom: 0; }
.home-table .table thead th {
  background: var(--blue-50); padding: 10px 10px; font-size: 12px; font-weight: 600;
  color: #475569; text-align: left; border-bottom: 1px solid var(--border);
}
.home-table .table tbody td {
  height: 42px; padding: 6px 10px; vertical-align: middle;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  border-bottom: 1px solid rgba(14,165,233,0.06); color: var(--text-main); font-size: 13px;
  transition: background .15s;
}
.home-table .table tbody tr:hover td { background: var(--blue-50); }
.col-customer { width: 196px; }
.col-contract { width: 128px; }
.col-code { width: 144px; }
.col-date { width: 86px; }
.col-amount { width: 114px; }
.col-status { width: 100px; }
.col-index { width: 40px !important; text-align: center; color: #94a3b8; font-variant-numeric: tabular-nums; font-size: 12px; }
.text-right { text-align: right; }
.amount-cell { font-variant-numeric: tabular-nums; color: #0ea5e9; font-weight: 600; }
.empty { padding: 24px 0; text-align: center; color: #94a3b8; white-space: normal; font-size: 13px; }
.home-table a { color: #0ea5e9; text-decoration: none; }
.home-table a:hover { text-decoration: underline; }

.status-pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.status-pill { background: var(--blue-50); color: #0ea5e9; }
.status-pill.warning { background: #fff7ed; color: #ea580c; }
.status-pill.danger { background: #fef2f2; color: #dc2626; }
.status-pill.success { background: #eff6ff; color: #0284c7; }

@media (max-width: 1200px) { .metric-grid { grid-template-columns: repeat(3, minmax(0,1fr)); } }
@media (max-width: 991px) {
  .metric-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .two-col { flex-direction: column; }
  .home-lists { grid-template-columns: 1fr; }
  .charts-row { flex-direction: column; }
}
@media (max-width: 640px) { .metric-grid { grid-template-columns: 1fr; } .home-hero h3 { font-size: 20px; } }
</style>

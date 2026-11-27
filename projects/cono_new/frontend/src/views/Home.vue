<template>
  <div class="home-page">
    <!-- 欢迎横幅 -->
    <div class="home-hero">
      <div class="hero-glow glow-1"></div>
      <div class="hero-glow glow-2"></div>
      <span class="hero-label"><el-icon><Monitor /></el-icon>业务工作台</span>
      <h3>欢迎回来，{{ user?.name || user?.username }}</h3>
      <p class="hero-sub">今天是 {{ todayText }} · {{ heroSub }}</p>
      <div class="hero-actions">
        <el-button v-if="canSee('contract')" type="primary" @click="router.push('/contract')" class="btn-cyber">
          <el-icon><Document /></el-icon>&nbsp;合同管理
        </el-button>
        <el-button v-if="canSee('collection')" type="primary" @click="router.push('/collection')" class="btn-cyber">
          <el-icon><Money /></el-icon>&nbsp;回款登记
        </el-button>
        <el-button v-if="canSee('plan')" type="primary" @click="router.push('/plan')" class="btn-cyber">
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
          <div class="metric-note" :class="item.noteClass">{{ item.note }}</div>
        </div>
      </div>
    </div>

    <!-- 图表 -->
    <div class="charts-row" v-if="canSee('chart')">
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
      <a class="quick-card" v-for="menu in visibleQuickMenus" :key="menu.title" :href="menu.url">
        <span class="quick-icon"><el-icon><component :is="menu.icon" /></el-icon></span>
        <span class="quick-name">{{ menu.title }}</span>
      </a>
    </div>

    <!-- 数据列表：最新合同 / 最新回款 / 最新发票 / 最新生产计划 / 最新售后 / 最新维修 / 最新返件 -->
    <div class="home-lists">
      <div class="panel home-table" v-if="canSee('contract')">
        <div class="panel-heading"><el-icon><Document /></el-icon><span>最新合同</span><router-link to="/contract" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-contract">合同号</th><th class="col-customer">客户</th><th>业务员</th><th class="col-date">日期</th><th class="col-amount">金额</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentContracts" :key="row.id">
              <td class="col-index"><span class="rank">{{ i + 1 }}</span></td>
              <td><router-link :to="`/contract/${row.id}`">{{ row.contract_number }}</router-link></td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td>{{ row.saler_name }}</td>
              <td>{{ row.date }}</td>
              <td class="amount-cell">{{ fmt(row.total_price) }}</td>
            </tr>
            <tr v-if="!recentContracts.length"><td colspan="6" class="empty">暂无合同数据</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table" v-if="canSee('collection')">
        <div class="panel-heading"><el-icon><Money /></el-icon><span>最新回款</span><router-link to="/collection" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-contract">合同</th><th class="col-date">日期</th><th class="col-amount">金额</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentCollections" :key="row.id">
              <td class="col-index"><span class="rank">{{ i + 1 }}</span></td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td><router-link :to="`/contract/${row.contract_id}`">{{ row.contract_number }}</router-link></td>
              <td>{{ row.date }}</td>
              <td class="amount-cell">{{ fmt(row.amount) }}</td>
            </tr>
            <tr v-if="!recentCollections.length"><td colspan="5" class="empty">暂无回款数据</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table" v-if="canSee('invoice')">
        <div class="panel-heading"><el-icon><List /></el-icon><span>最新发票</span><router-link to="/invoice" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-contract">合同</th><th class="col-date">日期</th><th class="col-amount">金额</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentInvoices" :key="row.id">
              <td class="col-index"><span class="rank">{{ i + 1 }}</span></td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td><router-link :to="`/contract/${row.contract_id}`">{{ row.contract_number }}</router-link></td>
              <td>{{ row.date }}</td>
              <td class="amount-cell">{{ fmt(row.amount) }}</td>
            </tr>
            <tr v-if="!recentInvoices.length"><td colspan="5" class="empty">暂无发票数据</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table" v-if="canSee('plan')">
        <div class="panel-heading"><el-icon><Calendar /></el-icon><span>最新生产计划</span><router-link to="/plan" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-contract">合同</th><th class="col-code">产品</th><th class="col-code">型号</th><th class="col-date">交货日期</th><th class="col-status">状态</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in upcomingPlans" :key="row.id" :class="{ 'is-overdue': row.is_overdue }">
              <td class="col-index"><span class="rank">{{ i + 1 }}</span></td>
              <td><router-link :to="`/contract/${row.contract_id}`">{{ row.contract_number }}</router-link></td>
              <td>{{ row.productcategory_name }}</td>
              <td :title="row.product_model">{{ row.product_model }}</td>
              <td :class="{ 'overdue-date': row.is_overdue }">{{ row.delivery_date }}</td>
              <td><span class="status-pill" :class="statusClass(row.completed_status)">{{ row.completed_status_display }}</span></td>
            </tr>
            <tr v-if="!upcomingPlans.length"><td colspan="6" class="empty">暂无生产计划</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table" v-if="canSee('service')">
        <div class="panel-heading"><el-icon><PhoneFilled /></el-icon><span>最新售后服务</span><router-link to="/service" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-code">维修编号</th><th class="col-code">型号</th><th class="col-date">接收日期</th><th class="col-status">状态</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentServices" :key="row.id">
              <td class="col-index"><span class="rank">{{ i + 1 }}</span></td>
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

      <div class="panel home-table" v-if="canSee('servicedetail')">
        <div class="panel-heading"><el-icon><Setting /></el-icon><span>最新维修记录</span><router-link to="/servicedetail" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-code">维修编号</th><th class="col-code">型号</th><th>维修人</th><th class="col-date">完成时间</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentServiceDetails" :key="row.id">
              <td class="col-index"><span class="rank">{{ i + 1 }}</span></td>
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

      <div class="panel home-table" v-if="canSee('return_product')">
        <div class="panel-heading"><el-icon><RefreshLeft /></el-icon><span>最新售后返件</span><router-link to="/return-product" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-customer">客户</th><th class="col-code">维修编号</th><th>发货人</th><th class="col-date">发货时间</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentReturnProducts" :key="row.id">
              <td class="col-index"><span class="rank">{{ i + 1 }}</span></td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td><router-link :to="`/return-product`">{{ row.service_number }}</router-link></td>
              <td>{{ row.user_name }}</td>
              <td>{{ row.date }}</td>
            </tr>
            <tr v-if="!recentReturnProducts.length"><td colspan="5" class="empty">暂无售后返件数据</td></tr>
          </tbody>
        </table>
      </div>
      <div class="panel home-table" v-if="canSee('flow_out')">
        <div class="panel-heading"><el-icon><Van /></el-icon><span>最新寄给客户</span><router-link to="/flow/out" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-code">流转编号</th><th class="col-customer">客户</th><th class="col-code">产品序列号</th><th class="col-date">寄出日期</th><th class="col-status">状态</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentFlowOuts" :key="row.id">
              <td class="col-index"><span class="rank">{{ i + 1 }}</span></td>
              <td><router-link to="/flow/out">{{ row.flow_number }}</router-link></td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td :title="row.archive_serial">{{ row.archive_serial }}</td>
              <td>{{ row.ship_date }}</td>
              <td><span class="status-pill" :class="row.status === 1 ? 'warning' : 'success'">{{ row.status_display }}</span></td>
            </tr>
            <tr v-if="!recentFlowOuts.length"><td colspan="6" class="empty">暂无寄出记录</td></tr>
          </tbody>
        </table>
      </div>

      <div class="panel home-table" v-if="canSee('flow_return')">
        <div class="panel-heading"><el-icon><RefreshLeft /></el-icon><span>最新客户返回</span><router-link to="/flow/return" class="see-all">查看全部</router-link></div>
        <table class="table">
          <thead><tr><th class="col-index">#</th><th class="col-code">流转编号</th><th class="col-customer">客户</th><th class="col-code">产品序列号</th><th class="col-date">返回日期</th><th class="col-status">返回后状态</th></tr></thead>
          <tbody>
            <tr v-for="(row, i) in recentFlowReturns" :key="row.id">
              <td class="col-index"><span class="rank">{{ i + 1 }}</span></td>
              <td><router-link to="/flow/return">{{ row.flow_number }}</router-link></td>
              <td :title="row.customer_name">{{ row.customer_name }}</td>
              <td :title="row.archive_serial">{{ row.archive_serial }}</td>
              <td>{{ row.actual_return_date }}</td>
              <td><span class="status-pill" :class="row.result_status_display === '维修中' ? 'warning' : 'success'">{{ row.result_status_display }}</span></td>
            </tr>
            <tr v-if="!recentFlowReturns.length"><td colspan="6" class="empty">暂无返回记录</td></tr>
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
import { pickColors } from '../components/chartColors'
import {
  Monitor, Document, Money, Calendar, Briefcase, TrendCharts, List, User,
  PieChart, Grid, PhoneFilled, Tools, RefreshLeft, Setting, Van,
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
const recentFlowOuts = ref([])
const recentFlowReturns = ref([])
const charts = ref({ year_labels: [], year_values: [], pie_labels: [], pie_values: [], assembly_labels: [], assembly_values: [] })
const visible = ref({})

// 无权限的模块既不显示卡片也不显示表格，与后端门控保持一致
const canSee = (key) => visible.value[key] !== false

const quickMenus = [
  { title: '合同管理', url: '/contract', icon: Document, perm: 'contract' },
  { title: '回款登记', url: '/collection', icon: Money, perm: 'collection' },
  { title: '发票登记', url: '/invoice', icon: List, perm: 'invoice' },
  { title: '生产计划', url: '/plan', icon: Calendar, perm: 'plan' },
  { title: '客户管理', url: '/customer', icon: User, perm: 'customer' },
  { title: '应收应付', url: '/accounts', icon: TrendCharts, perm: 'chart' },
  { title: '售后服务', url: '/service', icon: Tools, perm: 'service' },
  { title: '维修服务', url: '/servicedetail', icon: Setting, perm: 'servicedetail' },
]

const visibleQuickMenus = computed(() => quickMenus.filter(m => canSee(m.perm)))

const heroSub = computed(() => {
  const names = [
    ['contract', '合同'], ['collection', '回款'], ['invoice', '发票'],
    ['plan', '生产计划'], ['delivery', '发货'],
  ].filter(([k]) => canSee(k)).map(([, n]) => n)
  return names.length ? `${names.join('、')}数据已实时汇总` : '暂无业务数据权限，请联系管理员'
})

const fmt = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const metricCards = computed(() => {
  const cards = []
  if (canSee('contract')) cards.push({ label: '本年度合同', formatted: '¥' + fmt(metrics.value.year_contract_amount), note: metrics.value.year_contract_count + ' 份', icon: Document })
  if (canSee('collection')) cards.push({ label: '本季度回款', formatted: '¥' + fmt(metrics.value.quarter_collection_amount), note: metrics.value.quarter_collection_count + ' 笔记录', icon: TrendCharts })
  if (canSee('invoice')) cards.push({ label: '本月发票', formatted: '¥' + fmt(metrics.value.month_invoice_amount), note: metrics.value.month_invoice_count + ' 张登记', icon: List })
  if (canSee('plan')) {
    // 逾期数单独提示：待完工里最该被看见的是已经拖过交货日的那批
    const overdue = metrics.value.overdue_plans || 0
    cards.push({
      label: '待完工计划',
      formatted: (metrics.value.pending_plans || 0) + ' 条',
      note: overdue ? `${overdue} 条已逾期` : '全部在交期内',
      noteClass: overdue ? 'note-danger' : '',
      icon: Calendar,
    })
  }
  if (canSee('delivery')) cards.push({ label: '本月发货', formatted: metrics.value.month_delivery_qty + ' 件', note: metrics.value.month_delivery_count + ' 笔发货', icon: Money })
  return cards.map((c, i) => ({ ...c, color: i }))
})

const statusClass = (val) => val === 2 ? 'warning' : val === 3 ? 'success' : ''
const warrantyClass = (val) => val === 1 ? 'danger' : val === 2 ? 'warning' : 'success'

const yearChartOption = computed(() => {
  const colors = pickColors(charts.value.year_values.length)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 18, right: 18, top: 34, bottom: 28, containLabel: true },
    xAxis: {
      type: 'category', data: charts.value.year_labels,
      axisLine: { lineStyle: { color: 'rgba(0,120,224,0.2)' } },
      axisLabel: { color: '#4a5a6a', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#4a5a6a', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,120,224,0.06)' } },
    },
    series: [{
      name: '合同金额', type: 'bar', data: charts.value.year_values, barMaxWidth: 48,
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: (params) => {
          const c = colors[params.dataIndex % colors.length]
          return { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: c }, { offset: 1, color: c }] }
        },
      },
      emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,120,224,0.35)' } },
    }],
  }
})

// 电源装配图表当前未在首页展示（三图并排过挤），配置与接口数据保留，恢复时在模板加回 panel 即可。
// 柱色沿用首页业绩柱的取色方式：pickColors 随机打乱色环后逐柱分配。
const assemblyChartOption = computed(() => {
  const labels = charts.value.assembly_labels || []
  const values = charts.value.assembly_values || []
  const planFrom = charts.value.assembly_plan_from_year || 2023
  const colors = pickColors(values.length)
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        const year = Number(p.name)
        const source = year < planFrom ? '历史台账' : '生产计划'
        return `${p.name} 年<br/>电源装配：<b>${p.value}</b> 台<br/><span style="color:#909399;font-size:11px">数据来源：${source}</span>`
      },
    },
    grid: { left: 18, right: 18, top: 34, bottom: 28, containLabel: true },
    xAxis: {
      type: 'category', data: labels,
      axisLine: { lineStyle: { color: 'rgba(0,120,224,0.2)' } },
      axisLabel: { color: '#4a5a6a', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '台',
      nameTextStyle: { color: '#909399', fontSize: 11 },
      axisLabel: { color: '#4a5a6a', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,120,224,0.06)' } },
    },
    series: [{
      name: '电源装配数量', type: 'bar', data: values, barMaxWidth: 44,
      label: { show: true, position: 'top', color: '#4a5a6a', fontSize: 11 },
      labelLayout: { hideOverlap: true },
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: (params) => {
          const c = colors[params.dataIndex % colors.length]
          return { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: c }, { offset: 1, color: c }] }
        },
      },
      emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,120,224,0.35)' } },
    }],
  }
})

const pieChartOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: ¥{c}' },
  legend: {
    bottom: 0, type: 'scroll', orient: 'horizontal',
    textStyle: { color: '#4a5a6a', fontSize: 11 },
    itemWidth: 12, itemHeight: 8, pageIconSize: 8,
  },
  series: [{
    name: '销售业绩', type: 'pie', radius: ['38%', '64%'], center: ['50%', '44%'],
    avoidLabelOverlap: true, label: { color: '#4a5a6a', fontSize: 11 },
    data: charts.value.pie_labels.map((name, i) => ({ name, value: charts.value.pie_values[i] })),
    itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
    color: pickColors(charts.value.pie_labels.length),
    emphasis: { itemStyle: { shadowBlur: 14, shadowColor: 'rgba(0,120,224,0.3)' } },
  }],
}))

const load = async () => {
  try {
    const data = await request.get('/home/')
    todayText.value = data.today
    visible.value = data.visible || {}
    metrics.value = data.metrics || {}
    recentContracts.value = data.recent_contracts || []
    upcomingPlans.value = data.upcoming_plans || []
    recentCollections.value = data.recent_collections || []
    recentInvoices.value = data.recent_invoices || []
    recentServices.value = data.recent_services || []
    recentServiceDetails.value = data.recent_servicedetails || []
    recentReturnProducts.value = data.recent_return_products || []
    recentFlowOuts.value = data.recent_flow_outs || []
    recentFlowReturns.value = data.recent_flow_returns || []
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
  position: relative; overflow: hidden; border-radius: var(--radius-xl);
  padding: 32px 36px; margin-bottom: 22px;
  background: linear-gradient(120deg, var(--navy-900) 0%, var(--navy-800) 52%, #0a3f78 100%);
  border: 1px solid rgba(0,120,224,0.22);
  box-shadow: 0 1px 3px rgba(15,40,70,0.12), 0 12px 36px rgba(0,31,63,0.16);
}
.hero-glow { position: absolute; border-radius: 50%; pointer-events: none; }
.glow-1 { top: -60px; right: -40px; width: 260px; height: 260px; background: radial-gradient(circle, rgba(0,120,224,0.18) 0%, transparent 70%); }
.glow-2 { bottom: -80px; left: 30%; width: 200px; height: 200px; background: radial-gradient(circle, rgba(0,120,224,0.12) 0%, transparent 70%); }
.hero-label {
  display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px;
  border-radius: 999px; background: rgba(0,120,224,0.1); border: 1px solid rgba(0,120,224,0.3);
  color: var(--navy-300); font-size: 12px; font-weight: 600; letter-spacing: 1px;
}
.home-hero h3 { margin: 14px 0 6px; color: var(--text-bright); font-size: 26px; font-weight: 700; text-shadow: 0 0 24px rgba(0,120,224,0.3); }
.hero-sub { margin: 0; color: var(--navy-300); font-size: 13px; }
.hero-actions { margin-top: 18px; display: flex; gap: 8px; }
.btn-cyber {
  background: linear-gradient(135deg, var(--navy-500), var(--navy-700)) !important;
  border: none !important; color: #fff !important;
  box-shadow: 0 4px 16px rgba(0,120,224,0.35) !important;
}
.btn-outline {
  background: rgba(0,120,224,0.06) !important; border: 1px solid var(--border-bright) !important;
  color: var(--navy-500) !important;
}
.btn-outline:hover { background: var(--navy-50) !important; border-color: var(--navy-500) !important; }

/* ── 指标卡片 ── */
.metric-grid { display: grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap: 16px; margin-bottom: 22px; }
.home-card {
  position: relative; border-radius: var(--radius-lg); padding: 18px 20px;
  background: var(--bg-card); border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: transform var(--dur) var(--ease), box-shadow var(--dur) var(--ease),
              border-color var(--dur) var(--ease);
  overflow: hidden;
}
.home-card:hover {
  transform: translateY(-3px);
  border-color: var(--border-bright);
  box-shadow: var(--shadow-md);
}
.card-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.color-0 .card-accent { background: linear-gradient(90deg, var(--navy-500), transparent); }
.color-1 .card-accent { background: linear-gradient(90deg, var(--navy-600), transparent); }
.color-2 .card-accent { background: linear-gradient(90deg, #8b5cf6, transparent); }
.color-3 .card-accent { background: linear-gradient(90deg, #f59e0b, transparent); }
.color-4 .card-accent { background: linear-gradient(90deg, #d32f2f, transparent); }
.color-5 .card-accent { background: linear-gradient(90deg, var(--navy-500), transparent); }
.card-body { position: relative; z-index: 1; }
.metric-label { display: flex; align-items: center; gap: 6px; color: var(--text-sub); font-size: 12px; font-weight: 600; letter-spacing: .5px; }
.metric-label .el-icon { font-size: 14px; }
.color-0 .metric-label .el-icon { color: var(--navy-500); }
.color-1 .metric-label .el-icon { color: var(--navy-600); }
.color-2 .metric-label .el-icon { color: #8b5cf6; }
.color-3 .metric-label .el-icon { color: #f5a623; }
.color-4 .metric-label .el-icon { color: #d32f2f; }
.color-5 .metric-label .el-icon { color: var(--navy-500); }
.metric-value { margin-top: 10px; font-size: 26px; font-weight: 700; color: var(--text-main); line-height: 1.1; letter-spacing: -0.5px; }
.metric-note { margin-top: 5px; color: var(--text-dim); font-size: 11px; }
.metric-note.note-danger { color: #c62828; font-weight: 600; }

/* ── 图表行 ── */
.charts-row { display: flex; gap: 18px; margin-bottom: 22px; }
.panel {
  flex: 1; border-radius: var(--radius-lg); background: var(--bg-card);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm); overflow: hidden;
  transition: box-shadow var(--dur) var(--ease), border-color var(--dur) var(--ease);
}
.panel:hover { box-shadow: var(--shadow-md); border-color: var(--border-bright); }
.panel-heading {
  display: flex; align-items: center; gap: 8px; padding: 11px 18px;
  border-bottom: 1px solid var(--border-soft); color: var(--text-main);
  font-size: 13.5px; font-weight: 620;
}
.panel-heading .el-icon { color: var(--navy-500); font-size: 15px; }
.panel-hint { margin-left: auto; color: var(--text-dim); font-size: 11px; font-weight: 400; }
.panel-body { padding: 12px; }

/* 列表行首的模块色点：比整列图标轻，又能在长表格里快速定位模块 */
.home-table .panel-heading .el-icon {
  padding: 4px; border-radius: 6px; background: var(--navy-50);
  box-sizing: content-box;
}
.home-table .panel-heading .see-all {
  margin-left: auto; display: inline-flex; align-items: center; gap: 2px;
  font-size: 11.5px;
}
.home-table .panel-heading .see-all::after { content: '›'; font-size: 14px; line-height: 1; }

/* ── 常用功能 ── */
.section-title { display: flex; align-items: center; justify-content: space-between; margin: 22px 0 12px; }
.section-title h4 { display: flex; align-items: center; gap: 7px; margin: 0; color: var(--text-main); font-size: 15px; font-weight: 600; }
.section-title h4 .el-icon { color: var(--navy-500); }
.see-all { color: var(--navy-500); font-size: 12px; text-decoration: none; font-weight: 500; margin-left: auto; }
.see-all:hover { text-decoration: underline; }

.quick-grid { display: flex; gap: 12px; margin-bottom: 22px; flex-wrap: wrap; }
.quick-card {
  display: flex; align-items: center; padding: 12px 20px;
  border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--bg-card);
  color: var(--text-main); text-decoration: none; font-size: 13.5px; font-weight: 520;
  transition: all var(--dur) var(--ease); gap: 9px;
  box-shadow: var(--shadow-xs);
}
.quick-card:hover {
  border-color: var(--border-bright); background: var(--navy-50);
  transform: translateY(-2px); box-shadow: var(--shadow-sm);
}
.quick-icon {
  width: 34px; height: 34px; border-radius: var(--radius-sm); background: var(--navy-50);
  display: flex; align-items: center; justify-content: center; color: var(--navy-600);
  transition: all var(--dur) var(--ease);
}
.quick-card:hover .quick-icon { background: var(--navy-500); color: #fff; }

/* ── 表格 ── */
.two-col { display: flex; gap: 18px; margin-bottom: 18px; }
.home-lists { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 18px; margin-bottom: 18px; }
.home-table { border-radius: var(--radius-lg); background: var(--bg-card); border: 1px solid var(--border); overflow: hidden; box-shadow: var(--shadow-sm); }
.home-table .table { table-layout: fixed; width: 100%; border-collapse: collapse; margin-bottom: 0; }
/* 项目没有全局 box-sizing 重置，单元格默认 content-box：
   这里显式用 border-box，height 才是「整行」高度，不再被 padding 撑大。 */
.home-table .table thead th {
  background: var(--bg-subtle); padding: 0 12px; height: 30px; box-sizing: border-box;
  font-size: 11.5px; font-weight: 620;
  color: var(--text-sub); text-align: left; border-bottom: 1px solid var(--border-soft);
  letter-spacing: .2px; vertical-align: middle;
}
.home-table .table tbody td {
  height: 45px; padding: 0 12px; box-sizing: border-box; vertical-align: middle;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  border-bottom: 1px solid var(--border-soft); color: var(--text-main); font-size: 12.5px;
  transition: background var(--dur) var(--ease);
}
.home-table .table tbody tr:last-child td { border-bottom: none; }
.home-table .table tbody tr:hover td { background: var(--navy-50); }
.col-customer { width: 196px; }
.col-contract { width: 128px; }
.col-code { width: 144px; }
.col-date { width: 86px; }
.col-amount { width: 114px; }
.col-status { width: 100px; }
/* # 列居中：表头和单元格都要覆盖（th 的 text-align:left 优先级更高），
   并清掉左右 padding，否则不对称的内边距会让徽标偏离列中心。 */
.home-table .table thead th.col-index,
.home-table .table tbody td.col-index {
  width: 34px !important; padding: 0 !important; text-align: center;
  color: var(--text-dim); font-variant-numeric: tabular-nums; font-size: 11.5px;
}
/* 序号做成浅色小徽标，比纯数字更易扫读，又不喧宾夺主 */
.col-index span.rank {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 5px;
  background: var(--bg-subtle); color: var(--text-dim);
  font-size: 11px; font-weight: 600; line-height: 1;
}
.home-table tbody tr:hover .col-index span.rank { background: #fff; color: var(--navy-600); }
.text-right { text-align: right; }
.amount-cell { font-variant-numeric: tabular-nums; color: var(--navy-600); font-weight: 600; }
.empty { padding: 24px 0; text-align: center; color: var(--text-dim); white-space: normal; font-size: 13px; }
.home-table a { color: var(--navy-500); text-decoration: none; }
.home-table a:hover { text-decoration: underline; }

.status-pill {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 1px 9px; border-radius: 999px; font-size: 11px; font-weight: 600;
  background: var(--navy-50); color: var(--navy-600);
}
/* 状态点：颜色跟着状态语义走，比纯文字色块更容易在扫视时区分 */
.status-pill::before {
  content: ''; width: 5px; height: 5px; border-radius: 50%;
  background: currentColor; opacity: .75; flex: none;
}
.status-pill.warning { background: #fff7ed; color: #b45309; }
.status-pill.danger { background: #fef2f2; color: #b91c1c; }
.status-pill.success { background: #eef3f8; color: var(--navy-700); }
/* 逾期：交货日期已过还没完工，用红色左缘提示，不整行染色 */
.home-table tbody tr.is-overdue td:first-child { box-shadow: inset 2px 0 0 #e57373; }
.home-table tbody td.overdue-date { color: #c62828; font-weight: 600; }

@media (max-width: 1200px) { .metric-grid { grid-template-columns: repeat(3, minmax(0,1fr)); } }
@media (max-width: 991px) {
  .metric-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .two-col { flex-direction: column; }
  .home-lists { grid-template-columns: 1fr; }
  .charts-row { flex-direction: column; }
}
@media (max-width: 640px) { .metric-grid { grid-template-columns: 1fr; } .home-hero h3 { font-size: 20px; } }
</style>

<template>
  <div>
    <!-- 批量上传 -->
    <el-card shadow="never" class="upload-card">
      <template #header>
        <span class="card-title"><el-icon><Upload /></el-icon> 批量上传</span>
      </template>
      <div class="upload-row">
        <el-upload
          :action="uploadAction"
          :http-request="uploadFile"
          :show-file-list="false"
          :on-success="onUploadSuccess"
          :on-error="onUploadError"
          accept=".xlsx,.xls"
        >
          <el-button class="btn-import"><el-icon><Upload /></el-icon>&nbsp;选择文件</el-button>
        </el-upload>
        <el-button class="btn-export" @click="downloadTemplate"><el-icon><Download /></el-icon>&nbsp;模板下载</el-button>
      </div>
    </el-card>

    <!-- 工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-filter" @click="goContractList"><el-icon><Back /></el-icon>&nbsp;返回到合同列表</el-button>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="spacer"></span>
        <el-input
          v-model="keyword"
          placeholder="请输入客户名称或合同号或产品名称或型号..."
          clearable
          style="width: 320px"
          @keyup.enter="onSearch"
          @clear="onSearch"
        >
          <template #append>
            <el-button @click="onSearch"><el-icon><Search /></el-icon></el-button>
          </template>
        </el-input>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 合同产品展示</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="contract_order_number" label="ID" width="70" align="center" fixed />
        <el-table-column prop="customer_name" label="客户名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="category_name" label="产品名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="product_model" label="产品型号" min-width="130" show-overflow-tooltip />
        <el-table-column label="服务类型" width="95" align="center">
          <template #default="{ row }">
            <el-tag :type="row.contract_type === 'repair' ? 'warning' : 'success'" size="small">
              {{ row.contract_type_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="70" align="right" />
        <el-table-column prop="price" label="单价" width="100" align="right">
          <template #default="{ row }">¥{{ Number(row.price || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="total_price" label="金额" width="110" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ Number(row.total_price || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="contract_date" label="合同日期" width="105" align="center" />
        <el-table-column prop="contract_number" label="合同号" min-width="135" show-overflow-tooltip />
        <el-table-column prop="description" label="备注" min-width="150" show-overflow-tooltip />
      </el-table>
      <div class="pagination-row">
        <el-pagination
          v-model:current-page="page"
          :page-size="page_size"
          :total="total"
          layout="total, prev, pager, next, jumper"
          @current-change="fetchList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload, Download, Back, Search, List } from '@element-plus/icons-vue'
import request from '../../api/request'

const router = useRouter()

const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const keyword = ref('')

// action 走 el-upload 默认 ajax 需要完整路径；http-request 走 axios，baseURL 已是 /api
const uploadAction = '/api/contract-product/import/'
const uploadEndpoint = '/contract-product/import/'

// 走 axios 而非 el-upload 自带 ajax：复用统一拦截器，access token 过期时可静默刷新后重放
const uploadFile = ({ file }) => {
  const fd = new FormData()
  fd.append('file', file)
  return request.post(uploadEndpoint, fd)
}

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (keyword.value) params.keyword = keyword.value
    const data = await request.get('/contract-product/', { params })
    list.value = data.results || data
    total.value = data.count || list.value.length
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  page.value = 1
  fetchList()
}

const goContractList = () => router.push('/contract')
const exportData = () => window.open('/api/contract-product/export/', '_blank')
const downloadTemplate = () => window.open('/api/contract-product/template/', '_blank')

const onUploadSuccess = (res) => {
  ElMessage.success(res?.detail || '上传成功')
  fetchList()
}
// 错误提示由 request.js 响应拦截器统一弹出
const onUploadError = () => {}

onMounted(fetchList)
</script>

<style scoped>
.upload-card { margin-bottom: 12px; }
.toolbar-card { margin-bottom: 12px; }
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.upload-row { display: flex; align-items: center; gap: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; }
.spacer { flex: 1; }
.amount { font-weight: 600; color: #f56c6c; }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>

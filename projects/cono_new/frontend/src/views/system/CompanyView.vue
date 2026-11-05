<template>
  <div>
    <el-card shadow="never">
      <template #header><span class="card-title">公司信息</span></template>
      <el-form :model="form" label-width="140px" v-loading="loading">
        <el-row :gutter="16"><el-col :span="12"><el-form-item label="公司名称"><el-input v-model="form.company_name" /></el-form-item></el-col><el-col :span="12"><el-form-item label="公司税号"><el-input v-model="form.company_tax_number" /></el-form-item></el-col></el-row>
        <el-row :gutter="16"><el-col :span="12"><el-form-item label="银行账号"><el-input v-model="form.company_bank_account" /></el-form-item></el-col><el-col :span="12"><el-form-item label="开户行"><el-input v-model="form.company_bank" /></el-form-item></el-col></el-row>
        <el-row :gutter="16"><el-col :span="12"><el-form-item label="银行行号"><el-input v-model="form.company_bank_code" /></el-form-item></el-col><el-col :span="12"><el-form-item label="公司电话"><el-input v-model="form.company_phone" /></el-form-item></el-col></el-row>
        <el-row :gutter="16"><el-col :span="12"><el-form-item label="公司地址"><el-input v-model="form.company_address" /></el-form-item></el-col><el-col :span="12"><el-form-item label="公司传真"><el-input v-model="form.company_fax" /></el-form-item></el-col></el-row>
        <el-row :gutter="16"><el-col :span="12"><el-form-item label="公司邮箱"><el-input v-model="form.company_email" /></el-form-item></el-col><el-col :span="12"><el-form-item label="公司网址"><el-input v-model="form.company_website" /></el-form-item></el-col></el-row>
      </el-form>
      <el-button type="primary" :loading="saving" @click="handleSave" style="margin-top:12px">保存</el-button>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../../api/request'
const form = ref({}), loading = ref(false), saving = ref(false)
const fetchOne = async () => { loading.value = true; try { const d = await request.get("/company/"); form.value = (d.results && d.results[0]) || {} } finally { loading.value = false } }
const handleSave = async () => { saving.value = true; try { if (form.value.id) await request.put("/company/" + form.value.id + "/", form.value); else await request.post("/company/", form.value); ElMessage.success("保存成功") } finally { saving.value = false } }
onMounted(fetchOne)
</script>
<style scoped>.card-title{font-size:16px;font-weight:600;color:#303133}</style>
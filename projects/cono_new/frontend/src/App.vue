<template>
  <router-view />
</template>

<script setup>
</script>

<style>
/* ── 淡蓝科技主题全局变量 ── */
:root {
  --blue-50:    #f0f9ff;
  --blue-100:   #e0f2fe;
  --blue-200:   #bae6fd;
  --blue-300:   #7dd3fc;
  --blue-400:   #38bdf8;
  --blue-500:   #0ea5e9;
  --blue-600:   #0284c7;
  --blue-700:   #0369a1;

  --bg-body:       #eef6ff;
  --bg-surface:    #ffffff;
  --bg-card:       #ffffff;
  --bg-hover:      #f0f9ff;
  --border:        rgba(56,189,248,0.2);
  --border-bright: rgba(56,189,248,0.45);
  --accent:        #0ea5e9;
  --accent-glow:   rgba(14,165,233,0.2);
  --text-main:     #0c4a6e;
  --text-sub:      #475569;
  --text-dim:      #94a3b8;
  --danger:        #ef4444;
  --warn:          #f59e0b;
  --success:       #0ea5e9;
}

html, body, #app {
  margin: 0; padding: 0; height: 100%;
  font-family: 'Noto Sans SC', 'Helvetica Neue', Arial, sans-serif;
  background: var(--bg-body);
  color: var(--text-main);
  font-size: 12px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* Element Plus 基础字号统一为 12px */
:root {
  --el-font-size-base: 12px;
  --el-font-size-small: 12px;
  --el-font-size-extra-small: 12px;
  --el-font-size-large: 14px;
  --el-font-size-medium: 12px;
}

:deep(.el-card) {
  background: var(--bg-card) !important;
  border-color: var(--border) !important;
  color: var(--text-main) !important;
  box-shadow: 0 1px 4px rgba(14,165,233,0.06), 0 4px 16px rgba(14,165,233,0.04) !important;
}
:deep(.el-table) {
  background: var(--bg-card) !important;
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: var(--blue-50);
  --el-table-text-color: var(--text-sub);
  --el-table-header-text-color: var(--text-main);
  --el-table-border-color: var(--border);
  --el-table-row-hover-bg-color: var(--blue-50);
}
:deep(.el-menu) { background: transparent !important; }
:deep(.el-menu-item) { color: var(--text-sub) !important; }
:deep(.el-menu-item:hover) { background: var(--blue-50) !important; color: var(--blue-600) !important; }
:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, var(--blue-100), transparent) !important;
  color: var(--blue-700) !important;
  border-left: 3px solid var(--blue-400);
}
:deep(.el-input__wrapper) {
  background: var(--blue-50) !important;
  box-shadow: 0 0 0 1px var(--border) inset !important;
}
:deep(.el-input__inner) { color: var(--text-main) !important; }
:deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--blue-400), var(--blue-600)) !important;
  border-color: transparent !important;
  box-shadow: 0 4px 14px rgba(14,165,233,0.25) !important;
}
:deep(.el-button--info) {
  background: linear-gradient(135deg, var(--blue-500), var(--blue-700)) !important;
  border-color: transparent !important;
}
:deep(.el-button) { border-radius: 8px !important; font-size: 12px !important; }
:deep(.el-button--small) { font-size: 12px !important; }
:deep(.el-table) { font-size: 12px !important; }
:deep(.el-table th.el-table__cell) { font-size: 12px !important; }
:deep(.el-table td.el-table__cell) { font-size: 12px !important; }
:deep(.el-table .cell) { font-size: 12px !important; }
:deep(.el-input__inner) { font-size: 12px !important; }
:deep(.el-form-item__label) { font-size: 12px !important; }
:deep(.el-tag) { font-size: 12px !important; }
:deep(.el-pagination) { font-size: 12px !important; }
:deep(.el-pagination__total) { font-size: 12px !important; }
:deep(.el-descriptions) { font-size: 12px !important; }
:deep(.el-statistic__content) { font-size: 16px !important; }
:deep(.el-tabs__item) { font-size: 13px !important; }
:deep(.el-dropdown-menu__item) { font-size: 12px !important; }
:deep(.el-message) { font-size: 12px !important; }
:deep(.el-select-dropdown__item) { font-size: 12px !important; }
:deep(.el-dialog__title) { font-size: 15px !important; }
:deep(.el-card__header) { font-size: 13px !important; }
:deep(.el-radio__label) { font-size: 12px !important; }
:deep(.el-checkbox__label) { font-size: 12px !important; }
:deep(.el-date-editor .el-input__inner) { font-size: 12px !important; }
:deep(.el-progress__text) { font-size: 11px !important; }
:deep(.el-dropdown-menu) { background: var(--bg-card) !important; border-color: var(--border) !important; }
:deep(.el-dropdown-menu__item) { color: var(--text-main) !important; }
:deep(.el-dialog) { background: var(--bg-card) !important; border: 1px solid var(--border-bright) !important; }
:deep(.el-dialog__title) { color: var(--text-main) !important; }
:deep(.el-tabs__item) { color: var(--text-sub) !important; }
:deep(.el-tabs__item.is-active) { color: var(--blue-600) !important; }
:deep(.el-form-item__label) { color: var(--text-sub) !important; }
:deep(.el-popper) { background: var(--bg-card) !important; border-color: var(--border) !important; }
:deep(.el-popper .el-popper__arrow::before) { background: var(--bg-card) !important; border-color: var(--border) !important; }
:deep(.el-select-dropdown) { background: var(--bg-card) !important; border-color: var(--border) !important; }
:deep(.el-select-dropdown__item) { color: var(--text-main) !important; }
:deep(.el-select-dropdown__item.hover) { background: var(--blue-50) !important; }
:deep(.el-message) { background: var(--bg-card) !important; border-color: var(--border) !important; color: var(--text-main) !important; }
:deep(.el-loading-mask) { background: rgba(239,246,255,0.8) !important; }
:deep(.el-divider) { border-color: var(--border) !important; }
</style>

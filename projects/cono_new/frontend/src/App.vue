<template>
  <router-view />
</template>

<script setup>
</script>

<style>
/* ── NAURA 深海军蓝科技主题全局变量 ── */
:root {
  /* NAURA 品牌深蓝轴（主色调整体提亮一档） */
  --navy-900: #001f3f;
  --navy-800: #002b5c;
  --navy-700: #004a99;
  --navy-600: #005cc5;
  --navy-500: #0078e0;
  --navy-400: #1a8ce8;
  --navy-300: #4aa8f2;
  --navy-200: #7cc4f7;
  --navy-100: #d6ecff;
  --navy-50:  #eaf5ff;

  /* 背景层 */
  --bg-body:    #f4f6f9;
  --bg-surface: #ffffff;
  --bg-card:    #ffffff;
  --bg-hover:   #eef3f8;
  --bg-glass:   rgba(255,255,255,0.85);

  /* 边框与光效 */
  --border:        rgba(0,75,153,0.12);
  --border-bright: rgba(0,120,224,0.35);
  --border-glow:   rgba(0,120,224,0.20);
  --accent:        #0078e0;
  --accent-glow:   rgba(0,120,224,0.25);
  --glow-spread:   rgba(0,120,224,0.15);

  /* 文字层级 */
  --text-main:     #1a2533;
  --text-sub:      #4a5a6a;
  --text-dim:      #8a97a5;
  --text-bright:   #ffffff;

  /* 语义色（稳重低饱和） */
  --danger:  #d32f2f;
  --warn:    #f5a623;
  --success: #2e7d32;
  --info:    #0078e0;
}

html, body, #app {
  margin: 0; padding: 0; height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
  background: var(--bg-body);
  color: var(--text-main);
  font-size: 12px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
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
  box-shadow: 0 1px 4px rgba(0,0,0,0.35), 0 4px 16px rgba(0,0,0,0.25) !important;
  backdrop-filter: blur(6px);
}
:deep(.el-table) {
  background: var(--bg-card) !important;
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: var(--navy-50);
  --el-table-text-color: var(--text-sub);
  --el-table-header-text-color: var(--text-main);
  --el-table-border-color: var(--border);
  --el-table-row-hover-bg-color: var(--navy-50);
}
:deep(.el-menu) { background: transparent !important; }
:deep(.el-menu-item) { color: var(--text-sub) !important; }
:deep(.el-menu-item:hover) { background: var(--navy-50) !important; color: var(--navy-600) !important; }
:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, var(--navy-100), transparent) !important;
  color: var(--navy-700) !important;
  border-left: 3px solid var(--navy-500);
  box-shadow: 0 0 14px rgba(0,120,224,0.12);
}
:deep(.el-input__wrapper) {
  background: var(--bg-surface) !important;
  box-shadow: 0 0 0 1px var(--border) inset !important;
}
:deep(.el-input__inner) { color: var(--text-main) !important; }
:deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--navy-500), var(--navy-700)) !important;
  border-color: transparent !important;
  box-shadow: 0 4px 14px rgba(0,120,224,0.3) !important;
}
:deep(.el-button--info) {
  background: linear-gradient(135deg, var(--navy-600), var(--navy-800)) !important;
  border-color: transparent !important;
}
:deep(.el-button) { border-radius: 8px !important; font-size: 12px !important; color: var(--text-main) !important; }
:deep(.el-button--small) { font-size: 12px !important; }
:deep(.el-table) { font-size: 12px !important; }
:deep(.el-table th.el-table__cell) { font-size: 12px !important; color: var(--text-main) !important; }
:deep(.el-table td.el-table__cell) { font-size: 12px !important; color: var(--text-main) !important; }
:deep(.el-table .cell) { font-size: 12px !important; }
:deep(.el-input__inner) { font-size: 12px !important; }
:deep(.el-form-item__label) { font-size: 12px !important; color: var(--text-sub) !important; }
:deep(.el-tag) { font-size: 12px !important; background: var(--bg-surface) !important; border-color: var(--border) !important; color: var(--text-main) !important; }
:deep(.el-pagination) { font-size: 12px !important; color: var(--text-main) !important; }
:deep(.el-pagination__total) { font-size: 12px !important; color: var(--text-sub) !important; }
:deep(.el-descriptions) { font-size: 12px !important; }
:deep(.el-statistic__content) { font-size: 16px !important; color: var(--text-main) !important; }
:deep(.el-tabs__item) { font-size: 13px !important; color: var(--text-sub) !important; }
:deep(.el-dropdown-menu__item) { font-size: 12px !important; color: var(--text-main) !important; }
:deep(.el-message) { font-size: 12px !important; }
:deep(.el-dialog__title) { font-size: 15px !important; }
:deep(.el-card__header) { font-size: 13px !important; color: var(--text-main) !important; }
:deep(.el-radio__label) { font-size: 12px !important; color: var(--text-main) !important; }
:deep(.el-checkbox__label) { font-size: 12px !important; color: var(--text-main) !important; }
:deep(.el-date-editor .el-input__inner) { font-size: 12px !important; }
:deep(.el-progress__text) { font-size: 11px !important; color: var(--text-main) !important; }
:deep(.el-dropdown-menu) { background: var(--bg-card) !important; border-color: var(--border) !important; }
:deep(.el-dropdown-menu__item) { color: var(--text-main) !important; }
:deep(.el-dialog) { background: var(--bg-card) !important; border: 1px solid var(--border-bright) !important; box-shadow: 0 8px 32px rgba(0,0,0,0.45) !important; }
:deep(.el-dialog__title) { color: var(--text-main) !important; }
:deep(.el-tabs__item.is-active) { color: var(--navy-500) !important; }
:deep(.el-form-item__label) { color: var(--text-sub) !important; }
:deep(.el-popper) { background: var(--bg-card) !important; border-color: var(--border) !important; }
:deep(.el-popper .el-popper__arrow::before) { background: var(--bg-card) !important; border-color: var(--border) !important; }
:deep(.el-select-dropdown) { background: var(--bg-card) !important; border-color: var(--border) !important; }
:deep(.el-select-dropdown__item) { color: var(--text-main) !important; }
:deep(.el-select-dropdown__item.hover) { background: rgba(0,120,224,0.08) !important; }
:deep(.el-message) { background: var(--bg-card) !important; border-color: var(--border) !important; color: var(--text-main) !important; }
:deep(.el-loading-mask) { background: rgba(244,246,249,0.85) !important; }
:deep(.el-divider) { border-color: var(--border) !important; }
</style>

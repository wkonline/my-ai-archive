<template>
  <router-view />
</template>

<script setup>
</script>

<style>
/* ── Element Plus 全局视觉覆盖 ──
   本样式块为全局（无 scoped），因此不能使用 :deep()。
   直接书写 .el-* 选择器即可覆盖组件内部样式。 */

/* ── 卡片 ── */
.el-card {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--text-main) !important;
  box-shadow: var(--shadow-sm) !important;
  transition: border-color var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}
.el-card__header {
  padding: 13px 18px !important;
  border-bottom: 1px solid var(--border-soft) !important;
  font-size: 14px !important;
  font-weight: 620;
  color: var(--text-main) !important;
  background: transparent !important;
}
.el-card__body { padding: 16px 18px; }

/* ── 表格：浅蓝表头、细分隔线、悬浮高亮 ── */
.el-table {
  background: transparent !important;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: var(--bg-subtle);
  --el-table-text-color: var(--text-sub);
  --el-table-header-text-color: var(--text-main);
  --el-table-border-color: var(--border-soft);
  --el-table-row-hover-bg-color: var(--navy-50);
  font-size: 13px !important;
}
.el-table th.el-table__cell {
  background: var(--bg-subtle) !important;
  font-weight: 620 !important;
  font-size: 12.5px !important;
  color: var(--text-sub) !important;
  letter-spacing: .2px;
}
.el-table td.el-table__cell {
  border-bottom: 1px solid var(--border-soft) !important;
  color: var(--text-main) !important;
}
.el-table .cell { font-size: 13px !important; line-height: 1.5; }
.el-table--border .el-table__cell { border-right: 1px solid var(--border-soft) !important; }
.el-table__inner-wrapper::before { background-color: transparent !important; }

/* ── 输入框 / 选择器：柔和对焦光环 ── */
.el-input__wrapper,
.el-textarea__inner {
  background: var(--bg-surface) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: 0 0 0 1px var(--border) inset !important;
  transition: box-shadow var(--dur) var(--ease);
}
.el-input__wrapper:hover,
.el-textarea__inner:hover { box-shadow: 0 0 0 1px var(--border-bright) inset !important; }
.el-input__wrapper.is-focus,
.el-textarea__inner:focus {
  box-shadow: 0 0 0 1px var(--navy-400) inset, 0 0 0 3px rgba(0,120,224,0.12) !important;
}
.el-input__inner { color: var(--text-main) !important; font-size: 13px !important; }
.el-select__wrapper {
  border-radius: var(--radius-md) !important;
  box-shadow: 0 0 0 1px var(--border) inset !important;
  transition: box-shadow var(--dur) var(--ease);
}
.el-select__wrapper.is-focused {
  box-shadow: 0 0 0 1px var(--navy-400) inset, 0 0 0 3px rgba(0,120,224,0.12) !important;
}
.el-form-item__label { font-size: 13px !important; color: var(--text-sub) !important; }

/* ── 按钮 ── */
.el-button {
  border-radius: var(--radius-md) !important;
  font-size: 13px !important;
  font-weight: 520 !important;
  transition: all var(--dur) var(--ease);
}
.el-button--primary {
  background: linear-gradient(135deg, var(--navy-500), var(--navy-700)) !important;
  border-color: transparent !important;
  box-shadow: var(--shadow-brand) !important;
}
.el-button--primary:hover {
  background: linear-gradient(135deg, var(--navy-400), var(--navy-600)) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 22px rgba(0,120,224,0.30) !important;
}
.el-button--default {
  background: var(--bg-surface) !important;
  border-color: var(--border) !important;
  color: var(--text-sub) !important;
}
.el-button--default:hover {
  background: var(--navy-50) !important;
  border-color: var(--border-bright) !important;
  color: var(--navy-600) !important;
}

/* ── 标签：浅底圆角，弱化边框 ── */
.el-tag {
  border-radius: var(--radius-sm) !important;
  font-size: 12px !important;
  font-weight: 520;
  border-color: var(--border) !important;
  background: var(--bg-subtle) !important;
  color: var(--text-sub) !important;
}
.el-tag--primary, .el-tag--info {
  background: var(--navy-50) !important;
  border-color: var(--border-bright) !important;
  color: var(--navy-600) !important;
}

/* ── 分页 ── */
.el-pagination {
  font-size: 13px !important;
  color: var(--text-main) !important;
  --el-pagination-button-bg-color: transparent;
}
.el-pagination__total { font-size: 12.5px !important; color: var(--text-dim) !important; }
.el-pager li { border-radius: var(--radius-sm) !important; transition: all var(--dur) var(--ease); }
.el-pager li.is-active {
  background: linear-gradient(135deg, var(--navy-500), var(--navy-700)) !important;
  color: #fff !important;
}

/* ── 弹窗 / 抽屉：更柔和的投影 ── */
.el-dialog {
  background: var(--bg-card) !important;
  border-radius: var(--radius-xl) !important;
  box-shadow: var(--shadow-lg) !important;
  padding: 0 !important;
  overflow: hidden;
}
.el-dialog__header {
  padding: 18px 22px !important;
  margin: 0 !important;
  border-bottom: 1px solid var(--border-soft);
}
.el-dialog__title { font-size: 16px !important; font-weight: 640; color: var(--text-main) !important; }
.el-dialog__body { padding: 20px 22px !important; color: var(--text-main) !important; }
.el-dialog__footer { padding: 14px 22px 18px !important; border-top: 1px solid var(--border-soft); }
.el-overlay { backdrop-filter: blur(2px); background-color: rgba(15,30,50,0.42) !important; }

/* ── 下拉与浮层 ── */
.el-popper,
.el-select-dropdown,
.el-dropdown-menu {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border) !important;
  box-shadow: var(--shadow-md) !important;
  background: var(--bg-card) !important;
}
.el-dropdown-menu__item {
  font-size: 13px !important;
  color: var(--text-main) !important;
  border-radius: var(--radius-sm);
  margin: 2px 6px;
  transition: all var(--dur) var(--ease);
}
.el-dropdown-menu__item:hover { background: var(--navy-50) !important; color: var(--navy-600) !important; }
.el-select-dropdown__item { font-size: 13px !important; color: var(--text-main) !important; }
.el-select-dropdown__item.is-hovering { background: var(--navy-50) !important; }
.el-select-dropdown__item.is-selected { color: var(--navy-600) !important; font-weight: 600; }

/* ── 标签页 ── */
.el-tabs__item { font-size: 14px !important; color: var(--text-sub) !important; }
.el-tabs__item.is-active { color: var(--navy-500) !important; font-weight: 620; }
.el-tabs__active-bar { background: var(--navy-500) !important; height: 3px !important; border-radius: 2px; }

/* ── 其它细节 ── */
.el-message { border-radius: var(--radius-md) !important; box-shadow: var(--shadow-md) !important; font-size: 13px !important; }
.el-loading-mask { background: rgba(242,245,249,0.78) !important; backdrop-filter: blur(1px); }
.el-divider { border-color: var(--border-soft) !important; }
.el-descriptions { font-size: 13px !important; }
.el-descriptions__label { color: var(--text-sub) !important; font-weight: 520 !important; }
.el-descriptions__content { color: var(--text-main) !important; }
.el-empty__description p { color: var(--text-dim) !important; font-size: 13px; }
.el-statistic__content { font-size: 20px !important; color: var(--text-main) !important; }
.el-radio__label, .el-checkbox__label { font-size: 13px !important; color: var(--text-main) !important; }
.el-menu { background: transparent !important; border-right: none !important; }
</style>

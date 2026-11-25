/**
 * remote 搜索下拉的候选列表工具（客户、产品档案等）。
 *
 * 这些下拉都是 el-select 的 remote 模式：输入关键字就整体替换候选列表。
 * 由此产生两个真实故障：
 *   1. 编辑页只把当前选项塞进列表，用户改选其他项时搜不到（只能改回原选项）。
 *   2. 重新搜索时列表被整体替换，已选中的项不在结果里，el-select 找不到对应
 *      option，输入框就退化成一串 id。
 * 所以候选列表 = 本次搜索结果 ∪ 当前已选项。
 */

/**
 * 把已选项并入候选列表（去重，已选置顶）。
 *
 * @param {Array} list 原候选列表
 * @param {*} id 已选项 id
 * @param {string} label 已选项显示文本
 * @param {string} labelKey 显示文本字段名，客户是 company_name、档案是 serial_number
 */
export function mergeSelectedOption(list, id, label, labelKey = 'company_name') {
  if (!id || !label) return list
  if (list.some(item => item.id === id)) return list
  return [{ id, [labelKey]: label }, ...list]
}

/**
 * 用一次搜索结果替换候选列表，同时保留当前已选项。
 *
 * @param {Array} results 接口返回的数组
 * @param {*} selectedId 当前 form 里的选中 id
 * @param {Array} previous 替换前的候选列表（从中捞回已选项的显示文本）
 * @param {string} labelKey 显示文本字段名
 */
export function applySearchResults(results, selectedId, previous, labelKey = 'company_name') {
  const list = Array.isArray(results) ? results : []
  if (!selectedId) return list
  const hit = list.find(item => item.id === selectedId)
    || (previous || []).find(item => item.id === selectedId)
  if (!hit) return list
  return [hit, ...list.filter(item => item.id !== selectedId)]
}

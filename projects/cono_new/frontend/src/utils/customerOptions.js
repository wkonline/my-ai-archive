/**
 * 客户下拉的候选列表工具。
 *
 * 这些表单的客户下拉都是 el-select 的 remote 模式：输入关键字就整体替换候选列表。
 * 由此产生两个真实故障：
 *   1. 编辑页只把当前客户塞进列表，用户改选其他客户时搜不到（只能改回原客户）。
 *   2. 重新搜索时列表被整体替换，已选中的客户不在结果里，el-select 找不到对应
 *      option，输入框就退化成一串 id。
 * 所以候选列表 = 本次搜索结果 ∪ 当前已选客户。
 */

/** 把已选客户并入候选列表（去重，已选置顶）。 */
export function mergeSelectedCustomer(list, id, companyName) {
  if (!id || !companyName) return list
  if (list.some(item => item.id === id)) return list
  return [{ id, company_name: companyName }, ...list]
}

/**
 * 用一次搜索结果替换候选列表，同时保留当前已选客户。
 *
 * @param {Array} results 接口返回的客户数组
 * @param {*} selectedId 当前 form 里的客户 id
 * @param {Array} previous 替换前的候选列表（从中捞回已选客户的名称）
 */
export function applyCustomerResults(results, selectedId, previous) {
  const list = Array.isArray(results) ? results : []
  if (!selectedId) return list
  const hit = list.find(item => item.id === selectedId)
    || (previous || []).find(item => item.id === selectedId)
  if (!hit) return list
  return [hit, ...list.filter(item => item.id !== selectedId)]
}

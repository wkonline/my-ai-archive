import { onMounted, onBeforeUnmount } from 'vue'

// Element Plus 固定列宽度由 colgroup 内联 style 控制，CSS !important 无法覆盖内联。
// 此 composable 在移动端运行时用 JS 强行收窄固定列宽度，并取消 sticky 定位。
export function useMobileTableFix() {
  let timer = null
  let observer = null

  function apply() {
    const isMobile = window.innerWidth <= 768
    const rightW = isMobile ? '64px' : ''
    const leftW = isMobile ? '40px' : ''

    const rightSelectors = [
      '.el-table__fixed-right',
      '.el-table__fixed-right-header',
      '.el-table__fixed-right-body',
      '.el-table__fixed-right-patch',
    ]
    const leftSelectors = [
      '.el-table__fixed-left',
      '.el-table__fixed-left-header',
      '.el-table__fixed-left-body',
      '.el-table__fixed-left-patch',
    ]

    // 固定列容器
    rightSelectors.forEach(sel => {
      document.querySelectorAll(sel).forEach(el => {
        el.style.width = rightW
        el.style.minWidth = rightW
        el.style.maxWidth = rightW
        if (isMobile) {
          el.style.position = 'static'
          el.style.right = 'auto'
          el.style.left = 'auto'
          el.style.zIndex = 'auto'
        }
      })
    })
    leftSelectors.forEach(sel => {
      document.querySelectorAll(sel).forEach(el => {
        el.style.width = leftW
        el.style.minWidth = leftW
        el.style.maxWidth = leftW
        if (isMobile) {
          el.style.position = 'static'
          el.style.right = 'auto'
          el.style.left = 'auto'
          el.style.zIndex = 'auto'
        }
      })
    })

    // 固定列内部的 th / td
    document.querySelectorAll(
      '.el-table__fixed-right th, .el-table__fixed-right td, ' +
      '.el-table__fixed-left th, .el-table__fixed-left td'
    ).forEach(el => {
      const isRight = el.closest('.el-table__fixed-right')
      el.style.width = isRight ? rightW : leftW
      el.style.minWidth = isRight ? rightW : leftW
      el.style.maxWidth = isRight ? rightW : leftW
    })

    // colgroup col
    document.querySelectorAll('.el-table colgroup col').forEach(col => {
      // 无法可靠区分左右，统一在移动端收窄 gutter/固定列
    })
  }

  function schedule() {
    if (timer) clearTimeout(timer)
    timer = setTimeout(apply, 50)
  }

  onMounted(() => {
    apply()
    window.addEventListener('resize', schedule)
    observer = new MutationObserver(schedule)
    observer.observe(document.body, { childList: true, subtree: true })
  })

  onBeforeUnmount(() => {
    if (timer) clearTimeout(timer)
    window.removeEventListener('resize', schedule)
    if (observer) observer.disconnect()
  })
}
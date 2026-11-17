<template>
  <div ref="chartRef" :style="{ height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
// 按需引入 ECharts：项目只用到柱状/折线/饼图，避免整包 1MB+ 拖慢首屏
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  AxisPointerComponent,
  GridComponent,
  LegendPlainComponent,
  LegendScrollComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { WHEEL_12_COLORS } from './chartColors'

echarts.use([
  BarChart, LineChart, PieChart,
  AxisPointerComponent, GridComponent,
  LegendPlainComponent, LegendScrollComponent,
  TitleComponent, TooltipComponent,
  CanvasRenderer,
])

const props = defineProps({
  option: { type: Object, default: () => ({}) },
  height: { type: String, default: '300px' },
})

const chartRef = ref(null)
let chart = null

const render = () => {
  if (chart && props.option) chart.setOption(props.option, true)
}

onMounted(() => {
  chart = echarts.init(chartRef.value)
  chart.setOption({ color: WHEEL_12_COLORS }) // 默认调色板，供无显式颜色的系列使用
  render()
  window.addEventListener('resize', chart.resize)
})

watch(() => props.option, render, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', chart.resize)
  chart?.dispose()
})
</script>

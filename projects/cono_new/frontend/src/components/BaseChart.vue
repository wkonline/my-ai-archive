<template>
  <div ref="chartRef" :style="{ height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

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
  render()
  window.addEventListener('resize', chart.resize)
})

watch(() => props.option, render, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', chart.resize)
  chart?.dispose()
})
</script>

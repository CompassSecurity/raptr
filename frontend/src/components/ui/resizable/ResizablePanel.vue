<script setup lang="ts">
import { SplitterPanel, type SplitterPanelProps } from 'reka-ui'
import { ref } from 'vue'

const props = defineProps<SplitterPanelProps>()
const panel = ref<InstanceType<typeof SplitterPanel> | null>(null)

defineExpose({ panel })
</script>

<template>
  <SplitterPanel ref="panel" v-bind="props">
    <slot />
  </SplitterPanel>
</template>

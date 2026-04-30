<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next';
import { ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { reportService } from '@/services/reportService';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
}>();

const emit = defineEmits<(e: 'update:open', value: boolean) => void>();

const exporting = ref(false);
const sortBy = ref<string>('activity_position');
const sortOrder = ref<'asc' | 'desc'>('asc');

const handleExport = async () => {
    exporting.value = true;
    try {
        const { blob, filename } = await reportService.getReportContext(
            props.assessmentId,
            {
                sort_by: sortBy.value as
                    | 'activity_position'
                    | 'name'
                    | 'mitre_tactic'
                    | 'priority'
                    | 'state'
                    | 'start_time'
                    | 'coverage_score',
                sort_order: sortOrder.value,
            },
        );

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        toast.success('Results exported successfully');
        emit('update:open', false);
    } catch {
        // Error handled globally
    } finally {
        exporting.value = false;
    }
};

watch(
    () => props.open,
    (isOpen) => {
        if (isOpen) {
            sortBy.value = 'activity_position';
            sortOrder.value = 'asc';
        }
    },
);
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle>Export Results as JSON</DialogTitle>
        <DialogDescription>
          Configure sorting options to export the assessment results as a JSON file.
        </DialogDescription>
      </DialogHeader>

      <div class="flex flex-col gap-5 py-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <Label>Sort By</Label>
            <Select v-model="sortBy">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="activity_position">Position</SelectItem>
                <SelectItem value="name">Name</SelectItem>
                <SelectItem value="mitre_tactic">MITRE Tactic</SelectItem>
                <SelectItem value="priority">Priority</SelectItem>
                <SelectItem value="state">State</SelectItem>
                <SelectItem value="start_time">Start Time</SelectItem>
                <SelectItem value="coverage_score">Coverage Score</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="flex flex-col gap-2">
            <Label>Sort Order</Label>
            <Select v-model="sortOrder">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="asc">Ascending</SelectItem>
                <SelectItem value="desc">Descending</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="emit('update:open', false)" :disabled="exporting">
          Cancel
        </Button>
        <Button @click="handleExport" :disabled="exporting">
          <Loader2 v-if="exporting" class="mr-2 h-4 w-4 animate-spin" />
          {{ exporting ? 'Exporting...' : 'Export' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

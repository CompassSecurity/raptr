<script setup lang="ts">
import { FileText, Loader2 } from '@lucide/vue';
import { ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import { Badge } from '@/components/ui/badge';
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
import type { ReportTemplateRead } from '@/types/utils';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
}>();

const emit = defineEmits<(e: 'update:open', value: boolean) => void>();

const templates = ref<ReportTemplateRead[]>([]);
const loading = ref(false);
const generating = ref(false);
const selectedTemplateId = ref<string | null>(null);
const sortBy = ref<string>('activity_position');
const sortOrder = ref<'asc' | 'desc'>('asc');

async function fetchTemplates() {
    loading.value = true;
    try {
        templates.value = await reportService.getReportTemplates();
        // Auto-select first template if only one exists
        const first = templates.value[0];
        if (templates.value.length === 1 && first) {
            selectedTemplateId.value = first.id;
        }
    } catch {
        // Error handled globally
    } finally {
        loading.value = false;
    }
}

const handleGenerate = async () => {
    if (!selectedTemplateId.value) {
        toast.error('Please select a report template');
        return;
    }

    generating.value = true;
    try {
        const { blob, filename } = await reportService.generateReport(
            props.assessmentId,
            {
                template_id: selectedTemplateId.value,
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

        // Trigger browser download
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        toast.success('Report generated successfully');
        emit('update:open', false);
    } catch {
        // Error handled globally
    } finally {
        generating.value = false;
    }
};

watch(
    () => props.open,
    async (isOpen) => {
        if (isOpen) {
            selectedTemplateId.value = null;
            sortBy.value = 'activity_position';
            sortOrder.value = 'asc';
            await fetchTemplates();
        }
    },
);
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle>Generate Report</DialogTitle>
        <DialogDescription>
          Select a report template and configure sorting options to generate a report for this assessment.
        </DialogDescription>
      </DialogHeader>

      <div class="flex flex-col gap-5 py-4">
        <!-- Template Selection -->
        <div class="flex flex-col gap-2">
          <Label>Report Template</Label>

          <div v-if="loading" class="flex items-center justify-center h-24">
            <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
          </div>

          <div v-else-if="templates.length === 0" class="flex items-center justify-center h-24 rounded-md border border-dashed text-muted-foreground text-sm">
            No report templates available.
          </div>

          <div v-else class="flex flex-col gap-2">
            <div
              v-for="template in templates"
              :key="template.id"
              class="flex items-center gap-3 rounded-md border px-4 py-3 cursor-pointer transition-colors hover:bg-muted/50"
              :class="selectedTemplateId === template.id ? 'border-primary bg-primary/5' : 'border-border'"
              @click="selectedTemplateId = template.id"
            >
              <FileText class="h-4 w-4 shrink-0 text-muted-foreground" />
              <span class="flex-1 text-sm font-medium">{{ template.filename }}</span>
              <Badge variant="secondary" class="uppercase text-xs">{{ template.format }}</Badge>
            </div>
          </div>
        </div>

        <!-- Sort Options -->
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
        <Button variant="outline" @click="emit('update:open', false)" :disabled="generating">
          Cancel
        </Button>
        <Button @click="handleGenerate" :disabled="generating || !selectedTemplateId || loading">
          <Loader2 v-if="generating" class="mr-2 h-4 w-4 animate-spin" />
          {{ generating ? 'Generating...' : 'Generate Report' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

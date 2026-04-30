<script setup lang="ts">
import { ref } from 'vue';
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
import { Input } from '@/components/ui/input';
import { useAssessmentVariables } from '@/composables/useAssessmentVariables';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

// We initialize the composable here.
// Note: If assessmentId changes while this component is mounted, this instance won't update the key automatically
// unless we make the key reactive in the composable.
// However, typically the modal is closed and re-opened or the parent view handles ID changes by re-mounting or key-ing.
const { importVariables } = useAssessmentVariables(props.assessmentId);

const fileInput = ref<HTMLInputElement | null>(null);
const file = ref<File | null>(null);
const loading = ref(false);

const handleFileChange = (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
        file.value = target.files[0] ?? null;
    } else {
        file.value = null;
    }
};

const handleImport = async () => {
    if (!file.value) return;

    loading.value = true;
    try {
        const text = await file.value.text();
        // Re-initialize logic here in case assessmentId changed since mount?
        // For safety, we can get the fresh instance if we really wanted to, but simple is better.
        // Assuming ImportVariablesModal is keyed by assessmentId or re-created.

        // Actually, calling the composable inside the function is not standard/allowed for useStorage usually (setup only).
        // So we rely on correct props.

        const success = importVariables(text);

        if (success) {
            toast.success('Variables imported successfully');
            emit('success');
            emit('update:open', false);
            // Reset file
            file.value = null;
            if (fileInput.value) fileInput.value.value = '';
        } else {
            toast.error('Failed to import variables: Invalid JSON format');
        }
    } catch (error) {
        console.error('Import failed', error);
        toast.error('Failed to read file');
    } finally {
        loading.value = false;
    }
};
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>Import Variables</DialogTitle>
        <DialogDescription>
          Upload a JSON file containing key-value pairs for variable substitution.
          These variables are stored in your browser session and are scoped to this assessment.
        </DialogDescription>
      </DialogHeader>
      
      <div class="grid gap-4 py-4">
        <div class="grid w-full items-center gap-1.5">
          <Input 
            ref="fileInput"
            id="variables-file" 
            type="file" 
            accept=".json"
            @change="handleFileChange" 
          />
          <p class="text-xs text-muted-foreground mt-1">
            Expected format: <code>{"DOMAIN": "example.com", "USER": "admin"}</code>
          </p>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="$emit('update:open', false)">
          Cancel
        </Button>
        <Button type="submit" @click="handleImport" :disabled="!file || loading">
          {{ loading ? 'Importing...' : 'Import Variables' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

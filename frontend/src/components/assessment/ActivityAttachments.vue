<script setup lang="ts">
import {
    ChevronDown,
    Download,
    Paperclip,
    Trash2,
    Upload,
} from 'lucide-vue-next';
import { computed, onMounted, ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { fileService } from '@/services/fileService';
import { useAuthStore } from '@/stores/auth';
import type { FileRead } from '@/types/utils';

const props = defineProps<{
    assessmentId: string;
    activityId: string;
    refreshKey: number;
    readonly?: boolean;
}>();

const authStore = useAuthStore();
const files = ref<FileRead[]>([]);
const loadingFiles = ref(false);
const uploadingFile = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

function canDelete(file: FileRead): boolean {
    if (!props.readonly) return true;
    const role = authStore.getAssessmentRole(props.assessmentId);
    // Blue team can always delete blue files
    return role === 'blue' && file.category === 'blue';
}

const canUpload = computed(() => {
    if (!props.readonly) return true;
    const role = authStore.getAssessmentRole(props.assessmentId);
    return role === 'blue';
});

async function fetchFiles() {
    if (!props.activityId) return;
    loadingFiles.value = true;
    try {
        files.value = await fileService.getFiles(
            props.assessmentId,
            props.activityId,
        );
    } catch (e) {
        console.error('Failed to fetch files', e);
    } finally {
        loadingFiles.value = false;
    }
}

async function handleFileUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || !props.activityId) return;

    uploadingFile.value = true;
    try {
        await fileService.uploadFile(
            props.assessmentId,
            props.activityId,
            file,
        );
        toast.success(`File "${file.name}" uploaded successfully`);
        await fetchFiles();
    } catch (e) {
        console.error('Failed to upload file', e);
        toast.error('Failed to upload file');
    } finally {
        uploadingFile.value = false;
        input.value = '';
    }
}

async function handleFileDelete(file: FileRead) {
    if (!props.activityId) return;
    try {
        await fileService.deleteFile(
            props.assessmentId,
            props.activityId,
            file.id,
        );
        toast.success(`File "${file.filename}" deleted`);
        files.value = files.value.filter((f) => f.id !== file.id);
    } catch (e) {
        console.error('Failed to delete file', e);
        toast.error('Failed to delete file');
    }
}

async function handleFileDownload(file: FileRead) {
    if (!props.activityId) return;
    try {
        await fileService.downloadFile(
            props.assessmentId,
            props.activityId,
            file.id,
            file.filename,
        );
    } catch (e) {
        console.error('Failed to download file', e);
        toast.error('Failed to download file');
    }
}

function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

onMounted(() => fetchFiles());

watch(
    () => props.activityId,
    () => fetchFiles(),
);
watch(
    () => props.refreshKey,
    () => fetchFiles(),
);
</script>

<template>
    <Collapsible defaultOpen>
        <Card class="shadow-sm">
            <CollapsibleTrigger as-child>
                <CardHeader class="cursor-pointer hover:bg-muted/50 transition-colors">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <CardTitle class="text-lg">Attachments</CardTitle>
                            <Badge v-if="files.length > 0" variant="secondary" class="text-xs">{{ files.length }}</Badge>
                        </div>
                        <ChevronDown class="h-5 w-5 text-muted-foreground transition-transform duration-200 [[data-state=open]_&]:rotate-180" />
                    </div>
                </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
                <CardContent class="space-y-4">
                    <!-- Upload button -->
                    <div v-if="canUpload" class="flex items-center gap-3">
                        <input
                            ref="fileInputRef"
                            type="file"
                            accept=".png,.jpg,.jpeg,.txt"
                            class="hidden"
                            @change="handleFileUpload"
                        />
                        <Button
                            variant="outline"
                            size="sm"
                            @click="fileInputRef?.click()"
                            :disabled="uploadingFile"
                        >
                            <Upload v-if="!uploadingFile" class="mr-2 h-4 w-4" />
                            <span v-if="uploadingFile" class="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent inline-block"></span>
                            {{ uploadingFile ? 'Uploading...' : 'Upload File' }}
                        </Button>
                        <span class="text-xs text-muted-foreground">Supported: PNG, JPEG, TXT</span>
                    </div>

                    <!-- File list -->
                    <div v-if="loadingFiles" class="flex items-center justify-center py-6">
                        <span class="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
                        <span class="ml-2 text-sm text-muted-foreground">Loading files...</span>
                    </div>

                    <div v-else-if="files.length === 0" class="p-6 border border-dashed rounded-lg bg-muted/30 text-center">
                        <Paperclip class="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
                        <p class="text-sm text-muted-foreground">No files attached to this activity</p>
                    </div>

                    <div v-else class="space-y-2">
                        <div
                            v-for="file in files"
                            :key="file.id"
                            class="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                        >
                            <div class="flex items-center gap-3 min-w-0">
                                <Paperclip class="h-4 w-4 text-muted-foreground shrink-0" />
                                <div class="min-w-0">
                                    <p class="text-sm font-medium truncate">{{ file.filename }}</p>
                                    <p class="text-xs text-muted-foreground">
                                        {{ formatFileSize(file.size) }}
                                        <span class="mx-1">&middot;</span>
                                        <Badge variant="outline" class="text-xs px-1.5 py-0">{{ file.category }}</Badge>
                                    </p>
                                </div>
                            </div>
                            <div class="flex items-center gap-1 shrink-0">
                                <Button variant="ghost" size="sm" @click="handleFileDownload(file)">
                                    <Download class="h-4 w-4" />
                                </Button>
                                <Button v-if="canDelete(file)" variant="ghost" size="sm" @click="handleFileDelete(file)">
                                    <Trash2 class="h-4 w-4 text-destructive" />
                                </Button>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </CollapsibleContent>
        </Card>
    </Collapsible>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted, type ComponentPublicInstance } from 'vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Eye, Pencil, Upload } from 'lucide-vue-next';
import { useVModel } from '@vueuse/core';
import { cn } from '@/lib/utils'; // Assuming this exists as per shadcn-vue pattern, checked Textarea.vue

const props = withDefaults(defineProps<{
  modelValue?: string;
  label?: string;
  id?: string;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  onUpload?: (file: File) => Promise<string>;
  resolveImageUrl?: (url: string) => Promise<string>;
}>(), {
  modelValue: '',
  placeholder: 'Type markdown here...',
});

const emit = defineEmits<{
  (e: 'update:modelValue', payload: string): void;
}>();

const value = useVModel(props, 'modelValue', emit);
const isEditing = ref(false);
const isLoading = ref(false);
const textareaRef = ref<ComponentPublicInstance | null>(null);

// Configure marked
marked.use({
  async: false,
  gfm: true,
  breaks: true,
});

const previewRef = ref<HTMLElement | null>(null);
const blobUrlCache = new Map<string, string>();
const lightboxSrc = ref<string | null>(null);
const lightboxRef = ref<HTMLElement | null>(null);

function handlePreviewClick(event: MouseEvent) {
  const target = event.target as HTMLElement;
  if (target.tagName === 'IMG' && (target as HTMLImageElement).src) {
    event.stopPropagation();
    lightboxSrc.value = (target as HTMLImageElement).src;
    nextTick(() => lightboxRef.value?.focus());
    return;
  }
  
  // If the field is empty, clicking it should enter edit mode
  if (!value.value) {
    toggleMode();
  }
}

function closeLightbox() {
  lightboxSrc.value = null;
}

const renderedContent = computed(() => {
  if (!value.value) return '';
  let html = marked.parse(value.value) as string;
  html = DOMPurify.sanitize(html);
  // Move API image srcs to data attributes so they can be resolved with auth
  if (props.resolveImageUrl) {
    html = html.replace(
      /<img\s+src="(\/api\/[^"]+)"/g,
      '<img data-auth-src="$1"',
    );
  }
  return html;
});

async function resolveAuthImages() {
  if (!previewRef.value || !props.resolveImageUrl) return;
  const images = previewRef.value.querySelectorAll<HTMLImageElement>('img[data-auth-src]');
  for (const img of images) {
    const src = img.dataset.authSrc!;
    if (blobUrlCache.has(src)) {
      img.src = blobUrlCache.get(src)!;
      img.removeAttribute('data-auth-src');
      continue;
    }
    try {
      const blobUrl = await props.resolveImageUrl(src);
      blobUrlCache.set(src, blobUrl);
      img.src = blobUrl;
      img.removeAttribute('data-auth-src');
    } catch (e) {
      console.error('Failed to resolve image:', src, e);
      img.alt = 'Failed to load image';
      img.removeAttribute('data-auth-src');
    }
  }
}

watch([renderedContent, isEditing], async () => {
  if (isEditing.value || !props.resolveImageUrl) return;
  await nextTick();
  resolveAuthImages();
});

onMounted(async () => {
  if (!isEditing.value && props.resolveImageUrl) {
    await nextTick();
    resolveAuthImages();
  }
});

onUnmounted(() => {
  for (const url of blobUrlCache.values()) {
    URL.revokeObjectURL(url);
  }
});

function toggleMode() {
  if (props.disabled) return;
  isEditing.value = !isEditing.value;
  if (isEditing.value) {
    nextTick(() => {
        // Focus textarea if possible
        const el = textareaRef.value?.$el as HTMLElement;
         // If generic component wrapper, find textarea
        if (el?.tagName === 'TEXTAREA') {
            (el as HTMLTextAreaElement).focus();
        } else {
             const textarea = el?.querySelector('textarea');
             textarea?.focus();
        }
    });
  }
}

const handlePaste = async (event: ClipboardEvent) => {
  if (!props.onUpload) return;
  const items = event.clipboardData?.items;
  if (!items) return;

  for (const item of items) {
    if (item.type.indexOf('image') !== -1) {
      event.preventDefault();
      let file = item.getAsFile();
      if (!file) continue;

      // Rename generic clipboard names like "image.png" to something descriptive
      if (/^image\.\w+$/.test(file.name)) {
        const ext = file.name.split('.').pop();
        const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
        const rand = Math.random().toString(36).slice(2, 8);
        const newName = `paste-${ts}-${rand}.${ext}`;
        file = new File([file], newName, { type: file.type });
      }

      isLoading.value = true;
      try {
        const placeholder = `![Uploading ${file.name}...]()...`;

        let el = textareaRef.value?.$el as HTMLElement;
        if (el?.tagName !== 'TEXTAREA') {
             const found = el?.querySelector('textarea');
             if (found) el = found as HTMLElement;
        }
        const textarea = el as HTMLTextAreaElement;

        if (textarea) {
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const text = value.value;
            const before = text.substring(0, start);
            const after = text.substring(end);

            value.value = before + placeholder + after;
            await nextTick();

            const newCursorPos = start + placeholder.length;
            textarea.setSelectionRange(newCursorPos, newCursorPos);
            textarea.focus();

            const url = await props.onUpload(file);
            const imageMarkdown = `![${file.name}](${url})`;
            value.value = value.value.replace(placeholder, imageMarkdown);
        }
      } catch (error) {
        console.error('Upload failed', error);
        value.value = value.value.replace(/!\[Uploading.*?\]\(\)\.\.\./, '[Upload Failed]');
      } finally {
        isLoading.value = false;
      }
    }
  }
};
</script>

<template>
  <div :class="cn('flex flex-col gap-2 w-full group', className)">
    <div class="flex items-center justify-between mb-1 min-h-[24px]">
        <label v-if="label" :for="id" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">{{ label }}</label>
        <div class="flex items-center gap-2 ml-auto" v-if="!disabled">
             <Button
                type="button"
                variant="ghost"
                size="sm"
                class="h-6 px-2 text-xs flex gap-1 items-center hover:bg-muted"
                @click="toggleMode"
                :title="isEditing ? 'Switch to Preview' : 'Edit Markdown'"
            >
                <template v-if="isEditing">
                    <Eye class="h-3 w-3" />
                    <span>Preview</span>
                </template>
                <template v-else>
                    <Pencil class="h-3 w-3" />
                    <span>Edit</span>
                </template>
            </Button>
        </div>
    </div>

    <!-- View Mode -->
    <div
      v-if="!isEditing"
      ref="previewRef"
      class="min-h-[80px] w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm ring-offset-background md:text-sm prose dark:prose-invert max-w-none hover:bg-muted/20 cursor-pointer transition-colors"
      :class="{'cursor-default': disabled, 'text-muted-foreground italic': !value}"
      @click="handlePreviewClick"
    >
      <div v-if="value" class="markdown-content" v-html="renderedContent"></div>
      <div v-else class="select-none flex items-center gap-2">
         <Pencil class="h-3 w-3 opacity-50"/> <span>{{ placeholder }}</span>
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-else class="relative">
      <Textarea
        ref="textareaRef"
        v-model="value"
        :id="id"
        :placeholder="placeholder"
        :disabled="disabled || isLoading"
        class="min-h-[150px] font-mono resize-y"
        @paste="handlePaste"
        @keydown.esc="toggleMode"
      />
      <!-- Loading Overlay -->
      <div v-if="isLoading" class="absolute inset-0 bg-background/80 flex flex-col items-center justify-center rounded-md backdrop-blur-sm z-10">
        <Loader2 class="h-6 w-6 animate-spin text-primary" />
        <span class="text-xs text-muted-foreground mt-2">Uploading image...</span>
      </div>
       <div class="text-[10px] text-muted-foreground mt-1 flex gap-4 justify-between px-1">
            <span v-if="onUpload" class="flex items-center gap-1"><Upload class="h-3 w-3"/> Paste image to upload</span>
            <span v-else></span>
            <span>ESC to preview</span>
        </div>
    </div>

    <!-- Image Lightbox -->
    <Teleport to="body">
      <div
        v-if="lightboxSrc"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm cursor-zoom-out"
        @click="closeLightbox"
        @keydown.esc="closeLightbox"
        tabindex="0"
        ref="lightboxRef"
      >
        <img
          :src="lightboxSrc"
          class="max-w-[90vw] max-h-[90vh] object-contain rounded-lg shadow-2xl"
          @click.stop
        />
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* Basic Markdown Styles if prose is missing or incomplete */
.markdown-content :deep(h1) { font-size: 1.5em; font-weight: bold; margin-bottom: 0.5em; }
.markdown-content :deep(h2) { font-size: 1.3em; font-weight: bold; margin-bottom: 0.5em; margin-top: 1em; }
.markdown-content :deep(h3) { font-size: 1.1em; font-weight: bold; margin-bottom: 0.5em; margin-top: 1em; }
.markdown-content :deep(p) { margin-bottom: 0.5em; }
.markdown-content :deep(ul) { list-style-type: disc; padding-left: 1.5em; margin-bottom: 0.5em; }
.markdown-content :deep(ol) { list-style-type: decimal; padding-left: 1.5em; margin-bottom: 0.5em; }
.markdown-content :deep(a) { color: hsl(var(--primary)); text-decoration: underline; }
.markdown-content :deep(blockquote) { border-left: 4px solid hsl(var(--border)); padding-left: 1em; color: hsl(var(--muted-foreground)); font-style: italic; }
.markdown-content :deep(code) { 
  background-color: var(--code-inline-bg); 
  padding: 0.2em 0.4em; 
  border-radius: 0.375rem; 
  font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; 
  font-size: 0.875em; 
}
.markdown-content :deep(pre) { 
  background-color: var(--code-bg); 
  padding: 1rem; 
  border-radius: 0.375rem; 
  overflow-x: auto; 
  margin-bottom: 1rem; 
  border: 1px solid var(--code-border);
}
.markdown-content :deep(pre code) { 
  background-color: transparent; 
  padding: 0; 
  border: none;
  font-family: inherit;
  font-size: 100%;
}
.markdown-content :deep(img) { max-width: 100%; max-height: 400px; object-fit: contain; border-radius: 0.5rem; margin: 1em 0; cursor: zoom-in; }
.markdown-content :deep(table) { width: 100%; border-collapse: collapse; margin-bottom: 1em; }
.markdown-content :deep(th), .markdown-content :deep(td) { border: 1px solid hsl(var(--border)); padding: 0.5em; text-align: left; }
.markdown-content :deep(th) { background-color: hsl(var(--muted)); }
</style>

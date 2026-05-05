<script setup lang="ts">
import {
    AlertCircle,
    ArrowLeftRight,
    Check,
    ChevronDown,
    Copy,
    FileText,
    Loader2,
    Upload,
} from '@lucide/vue';
import { ref, watch } from 'vue';
import ImportVariablesModal from '@/components/assessment/ImportVariablesModal.vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAssessmentVariables } from '@/composables/useAssessmentVariables';
import { knowledgeBaseService } from '@/services/knowledgeBaseService';
import type { KnowledgeBaseRead } from '@/types/utils';

// Type for the structured KB content
interface KBTab {
    title: string;
    content: string;
}

interface KBSection {
    title: string;
    content?: string;
    tabs?: KBTab[];
}

interface KBContent {
    sections?: KBSection[];
}

const props = defineProps<{
    open: boolean;
    linkedArticles?: string[]; // Array of article names
    mitreTechniqueId?: string;
    assessmentId: string;
}>();

const emit = defineEmits<(e: 'update:open', value: boolean) => void>();

const loading = ref(false);
const articles = ref<KnowledgeBaseRead[]>([]);
const error = ref<string | null>(null);
const showImportVariables = ref(false);

// Fetch articles when modal opens or props change
watch(
    () => [props.open, props.linkedArticles, props.mitreTechniqueId],
    async ([isOpen]) => {
        if (isOpen) {
            await fetchArticles();
        }
    },
);

async function fetchArticles() {
    loading.value = true;
    error.value = null;
    articles.value = [];

    try {
        const hasLinked =
            props.linkedArticles && props.linkedArticles.length > 0;
        const hasMitre = !!props.mitreTechniqueId;

        if (!hasLinked && !hasMitre) {
            return;
        }

        // Build flat params (backend expects query params, not nested filters)
        const params: Record<string, unknown> = { limit: 100 };
        if (hasLinked) {
            params.names = props.linkedArticles;
        }
        if (hasMitre) {
            params.mitre_technique_id = props.mitreTechniqueId;
        }

        const response =
            await knowledgeBaseService.getKnowledgeBaseArticles(params);

        articles.value = response.items || [];
    } catch (e) {
        console.error('Failed to fetch KB articles', e);
        error.value =
            'Failed to load Knowledge Base articles. Please try again.';
    } finally {
        loading.value = false;
    }
}

// Parse KB content safely
function parseContent(content: unknown): KBContent | null {
    if (!content) return null;
    if (typeof content === 'object') return content as KBContent;
    return null;
}

// Check if content is structured (has sections) or is raw
function isStructuredContent(content: unknown): boolean {
    const parsed = parseContent(content);
    return (
        parsed !== null &&
        Array.isArray(parsed.sections) &&
        parsed.sections.length > 0
    );
}

// Fallback for unstructured content
function formatRawContent(content: unknown): string {
    if (typeof content === 'string') return content;
    try {
        return JSON.stringify(content, null, 2);
    } catch {
        return String(content);
    }
}

// Parse markdown-style content into segments (text vs code blocks)
interface ContentSegment {
    type: 'text' | 'code';
    content: string;
    language?: string;
}

function parseMarkdownContent(text: string): ContentSegment[] {
    if (!text || typeof text !== 'string') return [];

    const segments: ContentSegment[] = [];
    // Match ```language\ncode\n``` or ```code```
    const codeBlockRegex = /```(\w*)?\n?([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
        // Add text before the code block
        if (match.index > lastIndex) {
            const textContent = text.slice(lastIndex, match.index).trim();
            if (textContent) {
                segments.push({ type: 'text', content: textContent });
            }
        }
        // Add the code block
        segments.push({
            type: 'code',
            content: match[2]!.trim(),
            language: match[1] || undefined,
        });
        lastIndex = match.index + match[0].length;
    }

    // Add remaining text after last code block
    if (lastIndex < text.length) {
        const remainingText = text.slice(lastIndex).trim();
        if (remainingText) {
            segments.push({ type: 'text', content: remainingText });
        }
    }

    // If no code blocks found, return entire content as text
    if (segments.length === 0) {
        segments.push({ type: 'text', content: text });
    }

    return segments;
}

// Copy to clipboard
const copiedId = ref<string | null>(null);

async function copyToClipboard(text: string, id: string) {
    try {
        await navigator.clipboard.writeText(text);
        copiedId.value = id;
        setTimeout(() => {
            copiedId.value = null;
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
    }
}

// Switch action placeholder
const { processContent, hasVariables } = useAssessmentVariables(
    props.assessmentId,
);
const substitutedSegments = ref(new Set<string>());

function handleSwitch(id: string) {
    if (substitutedSegments.value.has(id)) {
        substitutedSegments.value.delete(id);
    } else {
        substitutedSegments.value.add(id);
    }
}

function getDisplayContent(content: string, id: string) {
    if (substitutedSegments.value.has(id)) {
        return processContent(content);
    }
    return content;
}
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="!w-[85vw] !max-w-[85vw] h-[85vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>Knowledge Base</DialogTitle>
        <DialogDescription>
          Related articles and documentation.
        </DialogDescription>
        <div class="absolute right-12 top-4 mr-4">
            <Button variant="outline" size="sm" @click="showImportVariables = true">
                <Upload class="mr-2 h-4 w-4" />
                Import Variables
            </Button>
        </div>
      </DialogHeader>

      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-4">
        <div class="rounded-lg border border-destructive/50 p-4 text-destructive">
          <div class="flex items-center gap-2 mb-1">
            <AlertCircle class="h-4 w-4" />
            <h5 class="font-medium leading-none tracking-tight">Error</h5>
          </div>
          <div class="text-sm opacity-90">
            {{ error }}
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="articles.length === 0" class="flex-1 flex flex-col items-center justify-center text-muted-foreground">
        <FileText class="h-12 w-12 mb-2 opacity-20" />
        <p>No related articles found.</p>
        <p class="text-xs pt-2">
          Technique: {{ mitreTechniqueId || 'None' }} 
          | Linked: {{ linkedArticles?.length || 0 }}
        </p>
      </div>

      <!-- Content with Tabs -->
      <div v-else class="flex-1 flex flex-col min-h-0">
        <Tabs :default-value="articles[0]?.id" class="flex-1 flex flex-col min-h-0">
          <div class="border-b px-1 shrink-0">
            <TabsList class="justify-start overflow-x-auto">
              <TabsTrigger 
                v-for="article in articles" 
                :key="article.id" 
                :value="article.id"
              >
                {{ article.name }}
              </TabsTrigger>
            </TabsList>
          </div>

          <div class="flex-1 min-h-0 relative mt-2">
            <TabsContent 
              v-for="article in articles" 
              :key="article.id" 
              :value="article.id"
              class="absolute inset-0 m-0 p-0 overflow-hidden flex flex-col data-[state=inactive]:hidden"
            >
              <ScrollArea class="h-full">
                <div class="p-4 space-y-6">
                  <!-- Header Info -->
                  <div class="flex items-center gap-4 text-sm text-muted-foreground border-b pb-3">
                    <span class="font-medium">MITRE ID: <span class="text-foreground">{{ article.mitre_technique_id || 'N/A' }}</span></span>
                  </div>

                  <!-- Structured Content -->
                  <template v-if="isStructuredContent(article.content)">
                    <div 
                      v-for="(section, sectionIndex) in parseContent(article.content)?.sections" 
                      :key="sectionIndex"
                      class="space-y-4"
                    >
                      <Collapsible :default-open="false">
                        <Card>
                          <CollapsibleTrigger as-child>
                            <CardHeader class="pb-3 cursor-pointer hover:bg-muted/50 transition-colors">
                              <div class="flex items-center justify-between">
                                <CardTitle class="text-lg">{{ section.title }}</CardTitle>
                                <ChevronDown class="h-5 w-5 text-muted-foreground transition-transform duration-200 [[data-state=open]_&]:rotate-180" />
                              </div>
                            </CardHeader>
                          </CollapsibleTrigger>
                          <CollapsibleContent>
                            <CardContent class="space-y-4">
                              <!-- Section Content with Markdown Code Block Parsing -->
                              <template v-if="section.content">
                                <template v-for="(segment, segIdx) in parseMarkdownContent(section.content)" :key="segIdx">
                                  <p v-if="segment.type === 'text'" class="text-sm text-muted-foreground whitespace-pre-wrap">
                                    {{ segment.content }}
                                  </p>
                                  <div v-else class="rounded-md bg-[var(--code-bg)] border border-[var(--code-border)] overflow-hidden my-4">
                                    <div class="flex items-center justify-end gap-1 px-2 py-1 border-b border-[var(--code-border)]">
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        class="h-6 w-6"
                                        @click.stop="copyToClipboard(getDisplayContent(segment.content, `section-${sectionIndex}-${segIdx}`), `section-${sectionIndex}-${segIdx}`)"
                                        title="Copy to clipboard"
                                      >
                                        <Check v-if="copiedId === `section-${sectionIndex}-${segIdx}`" class="h-3.5 w-3.5 text-green-500" />
                                        <Copy v-else class="h-3.5 w-3.5" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        class="h-6 w-6"
                                        @click.stop="handleSwitch(`section-${sectionIndex}-${segIdx}`)"
                                        :title="substitutedSegments.has(`section-${sectionIndex}-${segIdx}`) ? 'Show raw command' : 'Substitute variables'"
                                        :disabled="!hasVariables"
                                      >
                                        <ArrowLeftRight :class="['h-3.5 w-3.5', substitutedSegments.has(`section-${sectionIndex}-${segIdx}`) ? 'text-primary' : '']" />
                                      </Button>
                                    </div>
                                    <pre class="kb-code-block text-sm p-4 overflow-x-auto select-text cursor-text"><code>{{ getDisplayContent(segment.content, `section-${sectionIndex}-${segIdx}`) }}</code></pre>
                                  </div>
                                </template>
                              </template>

                              <!-- Section Tabs (nested procedures/methods) -->
                              <Tabs v-if="section.tabs && section.tabs.length > 0" :default-value="section.tabs[0]?.title" class="mt-4">
                                <TabsList class="justify-start">
                                  <TabsTrigger 
                                    v-for="tab in section.tabs" 
                                    :key="tab.title" 
                                    :value="tab.title"
                                    class="text-xs"
                                  >
                                    {{ tab.title }}
                                  </TabsTrigger>
                                </TabsList>
                                <TabsContent 
                                  v-for="tab in section.tabs" 
                                  :key="tab.title" 
                                  :value="tab.title"
                                  class="mt-3 space-y-3"
                                >
                                  <template v-for="(segment, segIdx) in parseMarkdownContent(tab.content)" :key="segIdx">
                                    <p v-if="segment.type === 'text'" class="text-sm text-muted-foreground whitespace-pre-wrap">
                                      {{ segment.content }}
                                    </p>
                                    <div v-else class="rounded-md bg-[var(--code-bg)] border border-[var(--code-border)] overflow-hidden my-4">
                                      <div class="flex items-center justify-end gap-1 px-2 py-1 border-b border-[var(--code-border)]">
                                        <Button
                                          variant="ghost"
                                          size="icon"
                                          class="h-6 w-6"
                                          @click.stop="copyToClipboard(getDisplayContent(segment.content, `tab-${tab.title}-${segIdx}`), `tab-${tab.title}-${segIdx}`)"
                                          title="Copy to clipboard"
                                        >
                                          <Check v-if="copiedId === `tab-${tab.title}-${segIdx}`" class="h-3.5 w-3.5 text-green-500" />
                                          <Copy v-else class="h-3.5 w-3.5" />
                                        </Button>
                                        <Button
                                          variant="ghost"
                                          size="icon"
                                          class="h-6 w-6"
                                          @click.stop="handleSwitch(`tab-${tab.title}-${segIdx}`)"
                                          :title="substitutedSegments.has(`tab-${tab.title}-${segIdx}`) ? 'Show raw command' : 'Substitute variables'"
                                          :disabled="!hasVariables"
                                        >
                                          <ArrowLeftRight :class="['h-3.5 w-3.5', substitutedSegments.has(`tab-${tab.title}-${segIdx}`) ? 'text-primary' : '']" />
                                        </Button>
                                      </div>
                                      <pre class="kb-code-block text-sm p-4 overflow-x-auto select-text cursor-text"><code>{{ getDisplayContent(segment.content, `tab-${tab.title}-${segIdx}`) }}</code></pre>
                                    </div>
                                  </template>
                                </TabsContent>
                              </Tabs>
                            </CardContent>
                          </CollapsibleContent>
                        </Card>
                      </Collapsible>
                    </div>
                  </template>

                  <!-- Raw/Unstructured Content Fallback -->
                  <template v-else>
                    <pre class="text-sm font-mono whitespace-pre-wrap bg-muted/50 p-4 rounded-md border text-foreground">{{ formatRawContent(article.content) }}</pre>
                  </template>
                </div>
              </ScrollArea>
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </DialogContent>
  </Dialog>

  <ImportVariablesModal
    v-model:open="showImportVariables"
    :assessment-id="assessmentId"
  />
</template>

<style scoped>
.kb-code-block {
  font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
  background-color: var(--code-bg, #f6f8fa);
  color: var(--foreground);
}

:deep(.kb-code-block code) {
  font-family: inherit;
  background-color: transparent;
  padding: 0;
  border: none;
  font-size: 100%;
}
</style>

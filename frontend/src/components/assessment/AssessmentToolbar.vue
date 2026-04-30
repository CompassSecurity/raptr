<script setup lang="ts">
import {
    ArrowUpDown,
    ChartArea,
    Download,
    FolderOpen,
    Folders,
    List,
    Plus,
    Server,
    Settings,
    Settings2,
    ShieldCheck,
    Trash,
    Upload,
} from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();

defineProps<{
    assessmentId?: string;
    assessmentName?: string;
    loading?: boolean;
    viewMode?: 'grouped' | 'flat';
    showDeleted?: boolean;
}>();

const emit = defineEmits<{
    (e: 'createActivity'): void;
    (e: 'createGroup'): void;
    (e: 'import', type: string): void;
    (e: 'export', type: string): void;
    (e: 'statistics'): void;
    (e: 'manageAssets'): void;
    (e: 'manage-assets'): void;
    (e: 'manage-order'): void;
    (e: 'manage-acl'): void;
    (e: 'manage-templates'): void;
    (e: 'update:viewMode', value: 'grouped' | 'flat'): void;
    (e: 'update:showDeleted', value: boolean): void;
}>();
</script>

<template>
  <div class="bg-muted/30 border-b">
    <div class="px-4 md:px-6 py-4">
      <div class="flex flex-col gap-4">
        <div v-if="!loading || assessmentName" class="flex items-center gap-2 flex-wrap">
          <Button v-if="authStore.hasAdminOrRedAccess(assessmentId)" size="sm" class="h-8" @click="emit('createActivity')">
            <Plus class="mr-2 h-4 w-4" />
            Create Activity
          </Button>
          <Button v-if="authStore.hasAdminOrRedAccess(assessmentId)" variant="secondary" size="sm" class="h-8" @click="emit('createGroup')">
            <FolderOpen class="mr-2 h-4 w-4" />
            Create Group
          </Button>

          <DropdownMenu v-if="authStore.hasAdminOrRedAccess(assessmentId)">
            <DropdownMenuTrigger as-child>
              <Button variant="outline" size="sm" class="h-8">
                <Upload class="mr-2 h-4 w-4" />
                Import
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem @click="emit('import', 'activity-template')">
                Activity(s) From Template
              </DropdownMenuItem>
              <DropdownMenuItem @click="emit('import', 'group-template')">
                Activity Group(s) From Template
              </DropdownMenuItem>
              <DropdownMenuItem @click="emit('import', 'campaign-template')">
                Campaign From Template
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="emit('import', 'variables')">
                Variables
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu v-if="authStore.hasAdminOrRedAccess(assessmentId)">
            <DropdownMenuTrigger as-child>
              <Button variant="outline" size="sm" class="h-8">
                <Download class="mr-2 h-4 w-4" />
                Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem v-if="authStore.hasAdminOrRedAccess(assessmentId)" @click="emit('export', 'results-json')">
                Results as JSON
              </DropdownMenuItem>

              <DropdownMenuItem v-if="authStore.hasAdminOrRedAccess(assessmentId)" @click="emit('export', 'generate-report')">
                Generate Report
              </DropdownMenuItem>
              <DropdownMenuItem v-if="authStore.hasAdminOrRedAccess(assessmentId)" @click="emit('export', 'mitre-navigator')">
                MITRE Navigator Layer
              </DropdownMenuItem>
              <DropdownMenuItem @click="emit('export', 'entire-assessment')">
                Entire Assessment
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Button variant="outline" size="sm" class="h-8" @click="emit('statistics')">
            <ChartArea class="mr-2 h-4 w-4" />
            Statistics
          </Button>
          <Button variant="outline" size="sm" class="h-8" @click="emit('manage-assets')">
            <Server class="mr-2 h-4 w-4" />
            Assets
          </Button>

          <DropdownMenu v-if="authStore.hasAdminOrRedAccess(assessmentId)">
            <DropdownMenuTrigger as-child>
              <Button variant="outline" size="sm" class="h-8">
                <Settings class="mr-2 h-4 w-4" />
                Manage
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem @click="emit('manage-order')">
                <ArrowUpDown class="mr-2 h-4 w-4" />
                Manage Order
              </DropdownMenuItem>
              <DropdownMenuItem v-if="authStore.user?.role === 'admin'" @click="emit('manage-acl')">
                <ShieldCheck class="mr-2 h-4 w-4" />
                Manage ACLs
              </DropdownMenuItem>
              <DropdownMenuItem @click="emit('manage-templates')">
                <Settings2 class="mr-2 h-4 w-4" />
                Default Templates
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <div class="h-6 w-px bg-border mx-1 hidden sm:block" />

          <div class="flex gap-1 border rounded-md p-1">
            <Button
              size="sm"
              :variant="viewMode === 'grouped' ? 'default' : 'ghost'"
              class="h-6 px-2"
              @click="emit('update:viewMode', 'grouped')"
              title="Grouped view"
            >
              <Folders class="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              :variant="viewMode === 'flat' ? 'default' : 'ghost'"
              class="h-6 px-2"
              @click="emit('update:viewMode', 'flat')"
              title="Flat view"
            >
              <List class="h-4 w-4" />
            </Button>
          </div>

          <!-- Show Deleted Toggle (Admin or Red Team) -->
          <Button
            v-if="authStore.hasAdminOrRedAccess(assessmentId)"
            :variant="showDeleted ? 'default' : 'outline'"
            size="sm"
            class="h-8"
            @click="emit('update:showDeleted', !showDeleted)"
          >
            <Trash class="h-4 w-4" />
          </Button>

        </div>
      </div>
    </div>
  </div>
</template>

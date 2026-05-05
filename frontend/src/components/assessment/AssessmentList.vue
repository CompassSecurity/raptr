<script setup lang="ts">
import { MoreVertical, Pencil, Trash } from '@lucide/vue';
import { onMounted } from 'vue';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import { useAssessmentListStore } from '@/stores/assessmentList';
import { useAuthStore } from '@/stores/auth';
import type { AssessmentRead } from '@/types/utils';

const authStore = useAuthStore();

const assessmentStore = useAssessmentListStore();

const emit = defineEmits<{
    (e: 'edit', assessment: AssessmentRead): void;
    (e: 'delete', assessment: AssessmentRead): void;
}>();

onMounted(() => {
    assessmentStore.fetchAssessments();
});
</script>

<template>
  <div>
    <div v-if="assessmentStore.loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card v-for="i in 6" :key="i" class="h-full">
        <CardHeader>
          <Skeleton class="h-6 w-2/3 mb-2" />
          <Skeleton class="h-4 w-full" />
        </CardHeader>
        <CardContent>
           <Skeleton class="h-10 w-full" />
        </CardContent>
        <CardFooter>
          <Skeleton class="h-5 w-20" />
        </CardFooter>
      </Card>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-fr">
      <Card v-for="assessment in assessmentStore.assessments" :key="assessment.id" class="hover:bg-muted/100 transition-colors h-full flex flex-col cursor-pointer group relative">
        <CardHeader class="flex flex-row items-start justify-between space-y-0 pb-2">
          <div class="space-y-1 pr-8">
            <CardTitle>{{ assessment.name }}</CardTitle>
            <CardDescription>{{ assessment.description }}</CardDescription>
          </div>
          <div class="absolute top-4 right-4">
            <DropdownMenu v-if="authStore.user?.role === 'admin'">
              <DropdownMenuTrigger as-child>
                <Button variant="ghost">
                  <MoreVertical class="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @click.stop="emit('edit', assessment)">
                  <Pencil class="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive" @click.stop="emit('delete', assessment)">
                  <Trash class="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent class="flex-1">
           <!-- Content could go here, maybe stats? -->
        </CardContent>
        <CardFooter>
          <Badge v-if="assessment.assessment_type === 'PurpleTeam'" variant="default"> 
              {{ assessment.assessment_type }}
          </Badge>
          <Badge v-else variant="destructive"> 
              {{ assessment.assessment_type }}
          </Badge>
        </CardFooter>
      </Card>

      <!-- Empty State -->
      <div v-if="assessmentStore.assessments.length === 0" class="col-span-full text-center py-12 text-gray-500">
        No assessments found.
      </div>
    </div>
  </div>
</template>

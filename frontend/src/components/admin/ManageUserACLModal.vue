<script setup lang="ts">
import { Loader2, Search } from 'lucide-vue-next';
import { computed, ref, watch } from 'vue';
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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { useAssessmentListStore } from '@/stores/assessmentList';
import type { AclRead, AssessmentRead, UserRead } from '@/types/utils';

const props = defineProps<{
    open: boolean;
    user: UserRead;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

const assessmentStore = useAssessmentListStore();

const localAcls = ref<AclRead[]>([]);
const loading = ref(false);
const searchQuery = ref('');

// Fetch data when modal opens
watch(
    () => props.open,
    async (isOpen) => {
        if (isOpen && props.user) {
            loading.value = true;
            try {
                // Fetch all assessments (limit to 1000 for now)
                await assessmentStore.fetchAssessments({ limit: 1000 });

                // Fetch current ACLs for this USER
                localAcls.value = await assessmentStore.fetchUserAcls(
                    props.user.id,
                );
            } catch (error) {
                toast.error('Failed to load data');
            } finally {
                loading.value = false;
            }
        }
    },
    { immediate: true },
);

const assessmentsWithRoles = computed(() => {
    if (!assessmentStore.assessments) return [];

    const term = searchQuery.value.toLowerCase();

    return assessmentStore.assessments
        .filter((assessment: AssessmentRead) =>
            assessment.name.toLowerCase().includes(term),
        ) // Client-side search
        .map((assessment: AssessmentRead) => {
            const acl = localAcls.value.find(
                (a) => a.assessment_id === assessment.id,
            );
            return {
                assessment,
                acl,
                currentRole: acl ? acl.assessment_role : 'none',
            };
        });
});

const handleRoleChange = async (
    assessmentId: string,
    newRole: string,
    currentAcl: AclRead | undefined,
) => {
    if (!props.user) return;

    loading.value = true;
    try {
        if (newRole === 'none') {
            // Delete if exists
            if (currentAcl) {
                await assessmentStore.deleteAcl(currentAcl.id);
                toast.success(
                    `Removed access for ${props.user.email} on ${currentAcl.assessment_id}`,
                ); // Ideally resolve assessment name but ID is fine for toast
            }
        } else {
            if (currentAcl) {
                // Update
                if (currentAcl.assessment_role !== newRole) {
                    await assessmentStore.updateAcl(currentAcl.id, {
                        user_id: props.user.id,
                        assessment_id: assessmentId,
                        assessment_role: newRole as
                            | 'red'
                            | 'blue'
                            | 'spectator',
                    });
                    toast.success(`Updated role to ${newRole}`);
                }
            } else {
                // Create
                await assessmentStore.createAcl({
                    user_id: props.user.id,
                    assessment_id: assessmentId,
                    assessment_role: newRole as 'red' | 'blue' | 'spectator',
                });
                toast.success(`Assigned ${newRole}`);
            }
        }

        // Refresh User ACLs
        localAcls.value = await assessmentStore.fetchUserAcls(props.user.id);
    } catch (error) {
        console.error(error);
    } finally {
        loading.value = false;
    }
};

const handleClose = () => {
    emit('update:open', false);
};
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[600px] max-h-[80vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>Manage User Access</DialogTitle>
        <DialogDescription>
          Manage assessment access for <strong>{{ user?.email }}</strong>.
        </DialogDescription>
      </DialogHeader>

      <div class="py-4 flex-1 overflow-hidden flex flex-col gap-4">
        <!-- Search -->
        <div class="relative">
          <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search assessments..." v-model="searchQuery" class="pl-8" />
        </div>

        <!-- Assessment List -->
        <div class="flex-1 overflow-y-auto min-h-0 border rounded-md">
            <div v-if="loading && !assessmentsWithRoles.length" class="p-8 flex justify-center">
                <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
            
            <Table v-else>
                <TableHeader class="bg-muted/50 sticky top-0">
                    <TableRow class="text-left">
                        <TableHead>Assessment</TableHead>
                        <TableHead class="w-[150px]">Role</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    <TableRow v-for="item in assessmentsWithRoles" :key="item.assessment.id">
                        <TableCell>
                            <div class="font-medium">{{ item.assessment.name }}</div>
                             <div class="text-xs text-muted-foreground">
                                {{ item.assessment.assessment_type }}
                            </div>
                        </TableCell>
                        <TableCell>
                            <Select
                                :model-value="item.currentRole || undefined"
                                @update:model-value="(val) => handleRoleChange(item.assessment.id, val as string, item.acl)"
                                :disabled="loading"
                            >
                                <SelectTrigger class="h-8">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="none">None</SelectItem>
                                    <SelectItem value="spectator">Spectator</SelectItem>
                                    <SelectItem value="blue">Blue Team</SelectItem>
                                    <SelectItem value="red">Red Team</SelectItem>
                                </SelectContent>
                            </Select>
                        </TableCell>
                    </TableRow>
                    <TableRow v-if="assessmentsWithRoles.length === 0 && !loading">
                        <TableCell colspan="2" class="p-8 text-center text-muted-foreground">
                            No assessments found.
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="handleClose">Close</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

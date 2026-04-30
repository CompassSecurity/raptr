<script setup lang="ts">
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const user = authStore.user;
</script>

<template>
    <Card class="mb-8 h-full overflow-hidden">
        <div class="h-32 w-full relative">
            <div class="absolute -bottom-12 left-1/2 -translate-x-1/2">
                <Avatar class="h-24 w-24 border-4 border-background">
                    <AvatarImage src="" />
                    <AvatarFallback class="text-2xl font-bold bg-primary text-primary-foreground">
                        {{ user?.email?.substring(0, 2).toUpperCase() }}
                    </AvatarFallback>
                </Avatar>
            </div>
        </div>
        <CardContent class="pt-16 pb-8 px-6 text-center space-y-6">
            <div class="space-y-2">
                <h3 class="text-2xl font-bold">{{ user?.email }}</h3>
                <p class="text-muted-foreground capitalize">{{ user?.role }}</p>
                <div class="pt-2">
                    <Badge :variant="user?.disabled ? 'destructive' : 'secondary'" class="rounded-full px-4">
                        {{ user?.disabled ? 'Disabled' : 'Active' }}
                    </Badge>
                </div>
            </div>
        </CardContent>
    </Card>
</template>
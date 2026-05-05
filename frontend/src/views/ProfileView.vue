<script setup lang="ts">
import { User } from '@lucide/vue';
import ProfileInformation from '@/components/profile/ProfileInformation.vue';
import ProfileResetMFA from '@/components/profile/ProfileResetMFA.vue';
import ProfileResetPassword from '@/components/profile/ProfileResetPassword.vue';
import ProfileTimeDateSettings from '@/components/profile/ProfileTimeDateSettings.vue';
</script>

<template>
    <div class="container mx-auto px-6 py-8">
        <div class="flex items-center justify-between mb-8">
            <div>
                <h1 class="text-3xl font-bold flex items-center gap-3">
                    <User class="w-8 h-8" />
                    Profile
                </h1>
                <p class="text-muted-foreground mt-2">Manage your profile information and settings.</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
            <ProfileInformation class="h-full" />
            <ProfileResetPassword class="h-full" />
            <ProfileTimeDateSettings class="h-full" />
            <ProfileResetMFA class="h-full" />
        </div>
    </div>
</template>
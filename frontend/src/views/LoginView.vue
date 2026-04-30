<script setup lang="ts">
import { toTypedSchema } from '@vee-validate/zod';
import { useForm } from 'vee-validate';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
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
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { useAuthStore } from '@/stores/auth';
import { schemas } from '@/types/zod';

const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);

const usernameInput = ref<InstanceType<typeof Input> | null>(null);

onMounted(() => {
    authStore.fetchProviders();
    usernameInput.value?.$el?.focus();
});

const formSchema = toTypedSchema(
    schemas.Body_login_api_v1_auth_token_post.pick({
        username: true,
        password: true,
    }),
);

const form = useForm({
    validationSchema: formSchema,
});

const onSubmit = form.handleSubmit(async (values) => {
    loading.value = true;
    try {
        const nextUrl = await authStore.login({
            username: values.username,
            password: values.password,
            scope: '',
        });

        if (nextUrl) {
            router.push(nextUrl);
        } else {
            router.push('/');
        }
    } catch (err) {
        // Error handled globally by API interceptor
    } finally {
        loading.value = false;
    }
});
</script>

<template>
  <div class="flex items-center justify-center min-h-screen p-4">
    <Card class="w-full max-w-md">
      <CardHeader class="space-y-1">
        <CardTitle class="text-2xl font-bold text-center">Sign In</CardTitle>
        <CardDescription class="text-center">
          Enter your username and password
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form @submit="onSubmit" class="space-y-4">
          <FormField v-slot="{ componentField }" name="username">
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input ref="usernameInput" type="text" placeholder="Enter your username" v-bind="componentField" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="password">
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" placeholder="Enter your password" v-bind="componentField" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <Button type="submit" class="w-full" :disabled="loading">
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter class="flex flex-col space-y-4">
        <div v-if="authStore.providers.length > 0" class="w-full space-y-2">
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <span class="w-full border-t" />
            </div>
            <div class="relative flex justify-center text-xs uppercase">
              <span class="bg-card px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>
          <Button 
            v-for="provider in authStore.providers" 
            :key="provider.name" 
            variant="outline" 
            class="w-full"
            @click="authStore.loginWithProvider(provider)"
          >
            {{ provider.name }}
          </Button>
        </div>
      </CardFooter>
    </Card>
  </div>
</template>


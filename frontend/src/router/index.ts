import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router';
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import AdminView from '@/views/AdminView.vue';
import AssessmentView from '@/views/AssessmentView.vue';
import ConfigurationView from '@/views/admin/ConfigurationView.vue';
import UserManagementView from '@/views/admin/UserManagementView.vue';
import HomeView from '@/views/HomeView.vue';
import LoginView from '@/views/LoginView.vue';
import ProfileView from '@/views/ProfileView.vue';

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView,
            meta: { requiresAuth: true },
        },
        {
            path: '/login',
            name: 'login',
            component: LoginView,
        },
        {
            path: '/auth/callback',
            name: 'auth-callback',
            component: () => import('@/views/AuthCallbackView.vue'),
        },
        {
            path: '/mfa',
            name: 'mfa-verify',
            component: () => import('@/views/auth/MfaVerifyView.vue'),
        },
        {
            path: '/mfa/setup',
            name: 'mfa-setup',
            component: () => import('@/views/auth/MfaSetupView.vue'),
        },
        {
            path: '/profile',
            name: 'profile',
            component: ProfileView,
            meta: { requiresAuth: true },
        },
        {
            path: '/admin',
            name: 'admin',
            component: AdminView,
            meta: { requiresAuth: true },
        },
        {
            path: '/admin/users',
            name: 'user-management',
            component: UserManagementView,
            meta: { requiresAuth: true },
        },
        {
            path: '/admin/configuration',
            name: 'configuration',
            component: ConfigurationView,
            meta: { requiresAuth: true },
        },
        {
            path: '/assessment/:id',
            name: 'assessment-detail',
            component: AssessmentView,
            meta: { requiresAuth: true },
        },
        {
            path: '/assessment/:id/statistics',
            name: 'assessment-statistics',
            component: () => import('@/views/AssessmentStatisticsView.vue'),
            meta: { requiresAuth: true },
        },
        {
            path: '/assessment/:id/:activityId',
            name: 'assessment-activity-detail',
            component: () => import('@/views/AssessmentActivityView.vue'),
            meta: { requiresAuth: true },
        },
        {
            path: '/assessment/:id/group/:groupId',
            name: 'assessment-group-detail',
            component: () => import('@/views/AssessmentActivityView.vue'),
            meta: { requiresAuth: true },
        },
    ],
});

router.beforeEach(
    async (
        to: RouteLocationNormalized,
        _from: RouteLocationNormalized,
        next: NavigationGuardNext,
    ) => {
        const authStore = useAuthStore();

        // Allow MFA routes even if user is not fully loaded, but token exists
        if (['/mfa', '/mfa/setup'].includes(to.path)) {
            if (!authStore.token) {
                return next('/login');
            }
            return next();
        }

        if (to.meta.requiresAuth && !authStore.token) {
            next('/login');
        } else {
            if (authStore.token && !authStore.user) {
                try {
                    await authStore.fetchMe();
                } catch (e) {
                    // handled in store (logout)
                }
            }
            next();
        }
    },
);

export default router;

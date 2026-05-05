import { type User as OidcUser, UserManager } from 'oidc-client-ts';
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { api } from '@/services/api';
import type {
    BodyLoginApiV1AuthTokenPost,
    MfaSetupResponse,
    Otp,
    Token,
    UserPasswordUpdate,
} from '@/types/types.gen';
import type { AclRole, ExternalAuthProvider, UserReadAcl } from '@/types/utils';

type LoginBody = BodyLoginApiV1AuthTokenPost;
type TokenResponse = Token;

export const useAuthStore = defineStore('auth', () => {
    const token = ref<string | null>(sessionStorage.getItem('token'));
    const user = ref<UserReadAcl | null>(null);
    const providers = ref<ExternalAuthProvider[]>([]);

    // Keep track of the UserManager instance
    let _userManager: UserManager | null = null;

    /**
     * Check if user has admin privileges or red team role for a specific assessment
     * @param assessmentId - The assessment ID to check ACL for (optional, if not provided only checks admin role)
     */
    const hasAdminOrRedAccess = computed(() => {
        return (assessmentId?: string): boolean => {
            // Global admins have access everywhere
            if (user.value?.role === 'admin') {
                return true;
            }

            // If no assessment ID provided, only check admin role
            if (!assessmentId) {
                return false;
            }

            // Check if user has red team role for this specific assessment
            return (
                user.value?.acl?.some(
                    (acl) =>
                        acl.assessment_id === assessmentId &&
                        acl.assessment_role === 'red',
                ) ?? false
            );
        };
    });

    /**
     * Get the user's ACL role for a specific assessment.
     * Returns 'red' for admins, or the actual role, or null if no access.
     */
    const getAssessmentRole = computed(() => {
        return (assessmentId?: string): AclRole | null => {
            if (!assessmentId) return null;
            if (user.value?.role === 'admin') return 'red' as AclRole;
            const acl = user.value?.acl?.find(
                (a) => a.assessment_id === assessmentId,
            );
            return (acl?.assessment_role as AclRole) ?? null;
        };
    });

    function setToken(newToken: string) {
        token.value = newToken;
        sessionStorage.setItem('token', newToken);
    }

    async function login(credentials: LoginBody): Promise<string | undefined> {
        // API expects application/x-www-form-urlencoded
        const formData = new URLSearchParams();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);
        if (credentials.grant_type)
            formData.append('grant_type', credentials.grant_type);
        if (credentials.scope) formData.append('scope', credentials.scope);
        if (credentials.client_id)
            formData.append('client_id', credentials.client_id);
        if (credentials.client_secret)
            formData.append('client_secret', credentials.client_secret);

        const response = await api.post<TokenResponse>(
            '/auth/token',
            formData,
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            },
        );

        if (response.data.access_token) {
            setToken(response.data.access_token);
            // If next_url is provided and not root, return it so the caller can redirect
            if (response.data.next_url && response.data.next_url !== '/') {
                return response.data.next_url;
            }
            // Otherwise, fetch user and return undefined
            await fetchMe();
        }
    }

    type MFASetupResponse = MfaSetupResponse;
    type OTPCheck = Otp;

    async function setupMfa(): Promise<MFASetupResponse> {
        const response = await api.post<MFASetupResponse>('/auth/mfa/setup');
        return response.data;
    }

    async function validateMfaSetup(code: string): Promise<string | undefined> {
        const body: OTPCheck = { otp: code };
        const response = await api.post<TokenResponse>(
            '/auth/mfa/setup/validate',
            body,
        );
        if (response.data.access_token) {
            setToken(response.data.access_token);
            if (response.data.next_url && response.data.next_url !== '/') {
                return response.data.next_url;
            }
            await fetchMe();
        }
    }

    async function verifyMfa(code: string): Promise<void> {
        const body: OTPCheck = { otp: code };
        const response = await api.post<TokenResponse>('/auth/mfa', body);
        if (response.data.access_token) {
            setToken(response.data.access_token);
            await fetchMe();
        }
    }

    async function fetchProviders() {
        try {
            const response =
                await api.get<ExternalAuthProvider[]>('/auth/providers');
            providers.value = response.data;
        } catch (error) {
            console.error('Failed to fetch providers', error);
        }
    }

    // Initialize or retrieve the UserManager for a given provider
    function getUserManager(provider: ExternalAuthProvider): UserManager {
        if (_userManager) {
            // Ideally we'd check if settings match, but for now we assume provider doesn't change
            // mid-session without full re-login.
            // If we really need to support switching providers dynamically without reload,
            // we could check _userManager.settings.authority etc.
            return _userManager;
        }

        _userManager = new UserManager({
            authority: provider.authority,
            client_id: provider.client_id,
            redirect_uri: `${window.location.origin}/auth/callback`,
            response_type: 'code',
            scope: provider.scope,
            automaticSilentRenew: true,
        });

        // Attach listener for silent renew
        _userManager.events.addUserLoaded((user) => {
            console.log('OIDC: User loaded (silent renew)', user);
            if (user.access_token) {
                setToken(user.access_token);
            }
        });

        _userManager.events.addAccessTokenExpiring(() => {
            console.log('OIDC: Access token expiring...');
        });

        _userManager.events.addAccessTokenExpired(() => {
            console.log('OIDC: Access token expired');
            // optionally logout or show warning
        });

        _userManager.events.addSilentRenewError((err) => {
            console.error('OIDC: Silent renew error', err);
        });

        return _userManager;
    }

    async function loginWithProvider(provider: ExternalAuthProvider) {
        const userManager = getUserManager(provider);

        sessionStorage.setItem('auth_provider', provider.name);
        await userManager.signinRedirect();
    }

    async function handleProviderCallback(): Promise<void> {
        const providerName = sessionStorage.getItem('auth_provider');
        if (!providerName) throw new Error('No provider session found');

        // Ensure providers are loaded to find the config
        if (providers.value.length === 0) {
            await fetchProviders();
        }

        const provider = providers.value.find((p) => p.name === providerName);
        if (!provider) throw new Error('Provider configuration not found');

        const userManager = getUserManager(provider);

        try {
            const oidcUser: OidcUser =
                await userManager.signinRedirectCallback();

            // Backend expects the access_token which contains the correct audience and azp claims
            // requested via the custom scope.
            const targetToken = oidcUser.access_token;

            if (targetToken) {
                setToken(targetToken);
                await fetchMe();
            }
        } catch (err) {
            console.error('OIDC Callback Error', err);
            throw err;
        } finally {
            // Do NOT remove auth_provider here if we want to support silent renew on reload?
            // Actually silent renew relies on oidc-client-ts storage (sessionStorage by default).
            // But we need to know WHICH provider config to use to re-instantiate UserManager on reload.
            // So we MUST leave 'auth_provider' in sessionStorage.
            // sessionStorage.removeItem('auth_provider'); // REMOVED
        }
    }

    /**
     * Re-initialize auth state on app load.
     * Checks if we have an active OIDC session and re-hooks up listeners.
     */
    async function initializeAuth() {
        const providerName = sessionStorage.getItem('auth_provider');
        if (!providerName) return; // No active OIDC provider session

        // We have a provider name, so we likely have an active OIDC session in storage.
        // We need to re-instantiate UserManager to attach event listeners.
        if (providers.value.length === 0) {
            await fetchProviders();
        }

        const provider = providers.value.find((p) => p.name === providerName);
        if (provider) {
            console.log(`Initializing OIDC for provider: ${providerName}`);
            const userManager = getUserManager(provider);

            // Check if we actually have a user
            try {
                const user = await userManager.getUser();
                if (user && !user.expired) {
                    console.log('OIDC session restored');
                    // Ensure token is synced just in case
                    if (
                        user.access_token &&
                        user.access_token !== token.value
                    ) {
                        setToken(user.access_token);
                    }
                } else {
                    console.log('OIDC session expired or not found');
                }
            } catch (e) {
                console.error('Error checking OIDC user', e);
            }
        }
    }

    async function fetchMe() {
        if (!token.value) return;
        try {
            const response = await api.get<UserReadAcl>('/user/me');
            user.value = response.data;
        } catch (error: any) {
            console.error('Fetch me failed', error);

            // Do not logout if the error is 403 due to MFA enforcement
            if (
                error?.response?.status === 403 &&
                typeof error.response.data?.detail === 'string'
            ) {
                const detail = error.response.data.detail;
                if (detail.includes('MFA setup required')) {
                    window.location.href = '/mfa/setup';
                    return;
                } else if (detail.includes('MFA required')) {
                    window.location.href = '/mfa';
                    return;
                }
            }

            logout();
        }
    }

    async function logout() {
        try {
            if (token.value) {
                await api.post('/auth/logout');
            }
        } catch (error) {
            // Ignore logout errors, still clear local session
            console.error('Logout API failed', error);
        } finally {
            token.value = null;
            user.value = null;
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('auth_provider'); // Clear provider on logout

            if (_userManager) {
                try {
                    // Try to signout redirect? Or just remove user?
                    // removeUser() clears the OIDC storage
                    await _userManager.removeUser();
                } catch (e) {
                    console.error(e);
                }
                _userManager = null;
            }

            // Cleanup OIDC artifacts just in case
            Object.keys(sessionStorage).forEach((key) => {
                if (key.startsWith('oidc.')) {
                    sessionStorage.removeItem(key);
                }
            });

            window.location.href = '/login';
        }
    }

    async function changePassword(data: UserPasswordUpdate) {
        await api.put('/user/me/password', data);
    }

    return {
        token,
        user,
        hasAdminOrRedAccess,
        getAssessmentRole,
        setToken,
        login,
        logout,
        fetchMe,
        changePassword,
        fetchProviders,
        loginWithProvider,
        handleProviderCallback,
        initializeAuth,
        providers,
        setupMfa,
        validateMfaSetup,
        verifyMfa,
    };
});

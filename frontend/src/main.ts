import { createPinia } from 'pinia';
import { configure } from 'vee-validate';
import { createApp } from 'vue';
import { z } from 'zod';
import router from './router';
import './style.css';
import App from './App.vue';

z.config({
    customError(issue) {
        if (issue.code === 'invalid_type' && issue.input === undefined) {
            return 'Required';
        }
    },
});

configure({
    validateOnBlur: false,
    validateOnChange: false,
    validateOnInput: false,
    validateOnModelUpdate: false,
});

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.mount('#app');

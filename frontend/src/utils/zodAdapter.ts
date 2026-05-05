import type { TypedSchema, TypedSchemaError } from 'vee-validate';
import type { input, output, ZodType } from 'zod';

export function toTypedSchema<T extends ZodType>(
    schema: T,
): TypedSchema<input<T>, output<T>> {
    return {
        __type: 'VVTypedSchema' as const,
        async parse(value) {
            const result = schema.safeParse(value);
            if (result.success) {
                return { value: result.data, errors: [] };
            }
            const errors: TypedSchemaError[] = result.error.issues.map(
                (issue) => ({
                    path: issue.path.map(String).join('.'),
                    errors: [issue.message],
                }),
            );
            return { errors };
        },
    };
}

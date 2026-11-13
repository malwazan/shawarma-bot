import { revalidateLogic } from "@tanstack/react-form";
import { useNavigate } from "@tanstack/react-router";
import { CircleAlert } from "lucide-react";
import { z } from "zod";
import { Alert, AlertDescription } from "#/components/ui/alert";
import { useLogin, useRegister } from "#/lib/api/auth";
import { getErrorMessage } from "#/lib/api/client";
import { useAppForm } from "#/lib/form";

// Mirrors the backend limits in backend/src/user/schemas.py
const name = z.string().trim().min(1, "Name is required").max(256);

const loginSchema = z.object({
	name,
	password: z.string().min(1, "Password is required").max(128),
});

const registerSchema = z
	.object({
		name,
		password: z
			.string()
			.min(8, "Password must be at least 8 characters")
			.max(128, "Password must be at most 128 characters"),
		confirmPassword: z.string().min(1, "Please confirm your password"),
	})
	.refine((v) => v.password === v.confirmPassword, {
		message: "Passwords don't match",
		path: ["confirmPassword"],
	});

// Validate on first submit, then re-validate as the user types.
const validationLogic = revalidateLogic({
	mode: "submit",
	modeAfterSubmission: "change",
});

function FormError({ error }: { error: unknown }) {
	if (!error) return null;
	return (
		<Alert variant="destructive">
			<CircleAlert />
			<AlertDescription>{getErrorMessage(error)}</AlertDescription>
		</Alert>
	);
}

export function LoginForm() {
	const navigate = useNavigate();
	const login = useLogin();

	const form = useAppForm({
		defaultValues: { name: "", password: "" },
		validationLogic,
		validators: { onDynamic: loginSchema },
		onSubmit: async ({ value }) => {
			try {
				await login.mutateAsync({
					name: value.name.trim(),
					password: value.password,
				});
				await navigate({ to: "/" });
			} catch {
				// Shown below via login.error
			}
		},
	});

	return (
		<form
			noValidate
			className="grid gap-4"
			onSubmit={(e) => {
				e.preventDefault();
				form.handleSubmit();
			}}
		>
			<FormError error={login.error} />
			<form.AppField name="name">
				{(field) => (
					<field.TextField label="Name" autoComplete="username" autoFocus />
				)}
			</form.AppField>
			<form.AppField name="password">
				{(field) => (
					<field.TextField
						label="Password"
						type="password"
						autoComplete="current-password"
					/>
				)}
			</form.AppField>
			<form.AppForm>
				<form.SubmitButton>Log in</form.SubmitButton>
			</form.AppForm>
		</form>
	);
}

export function RegisterForm() {
	const navigate = useNavigate();
	const register = useRegister();

	const form = useAppForm({
		defaultValues: { name: "", password: "", confirmPassword: "" },
		validationLogic,
		validators: { onDynamic: registerSchema },
		onSubmit: async ({ value }) => {
			try {
				await register.mutateAsync({
					name: value.name.trim(),
					password: value.password,
				});
				await navigate({ to: "/" });
			} catch {
				// Shown below via register.error
			}
		},
	});

	return (
		<form
			noValidate
			className="grid gap-4"
			onSubmit={(e) => {
				e.preventDefault();
				form.handleSubmit();
			}}
		>
			<FormError error={register.error} />
			<form.AppField name="name">
				{(field) => (
					<field.TextField label="Name" autoComplete="username" autoFocus />
				)}
			</form.AppField>
			<form.AppField name="password">
				{(field) => (
					<field.TextField
						label="Password"
						type="password"
						autoComplete="new-password"
					/>
				)}
			</form.AppField>
			<form.AppField name="confirmPassword">
				{(field) => (
					<field.TextField
						label="Confirm password"
						type="password"
						autoComplete="new-password"
					/>
				)}
			</form.AppField>
			<form.AppForm>
				<form.SubmitButton>Create account</form.SubmitButton>
			</form.AppForm>
		</form>
	);
}

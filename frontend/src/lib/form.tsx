import {
	createFormHook,
	createFormHookContexts,
	useSelector,
} from "@tanstack/react-form";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { type ComponentProps, type ReactNode, useState } from "react";
import { Button } from "#/components/ui/button";
import { Input } from "#/components/ui/input";
import { Label } from "#/components/ui/label";

export const { fieldContext, useFieldContext, formContext, useFormContext } =
	createFormHookContexts();

type TextFieldProps = { label: string } & Omit<
	ComponentProps<typeof Input>,
	"name" | "value" | "onChange" | "onBlur"
>;

function useFieldError() {
	const field = useFieldContext<string>();
	const errors = useSelector(field.store, (s) => s.meta.errors);
	const error = errors[0] as { message?: string } | string | undefined;
	return typeof error === "string" ? error : error?.message;
}

function TextField({ label, ...inputProps }: TextFieldProps) {
	const field = useFieldContext<string>();
	const message = useFieldError();

	return (
		<div className="grid gap-2">
			<Label htmlFor={field.name}>{label}</Label>
			<Input
				id={field.name}
				name={field.name}
				value={field.state.value}
				onChange={(e) => field.handleChange(e.target.value)}
				onBlur={field.handleBlur}
				aria-invalid={!!message}
				{...inputProps}
			/>
			{message && <p className="text-destructive text-sm">{message}</p>}
		</div>
	);
}

/** A masked input with an eye button that shows/hides the value. */
function SecretField({
	label,
	description,
	status,
	...inputProps
}: Omit<TextFieldProps, "type"> & {
	/** Help text under the input. */
	description?: ReactNode;
	/** Shown at the end of the label row, e.g. whether a value is saved. */
	status?: ReactNode;
}) {
	const field = useFieldContext<string>();
	const message = useFieldError();
	const [visible, setVisible] = useState(false);
	const descriptionId = `${field.name}-description`;

	return (
		<div className="grid gap-2">
			<div className="flex items-center justify-between gap-2">
				<Label htmlFor={field.name}>{label}</Label>
				{status}
			</div>
			<div className="relative">
				<Input
					id={field.name}
					name={field.name}
					type={visible ? "text" : "password"}
					value={field.state.value}
					onChange={(e) => field.handleChange(e.target.value)}
					onBlur={field.handleBlur}
					aria-invalid={!!message}
					autoComplete="off"
					spellCheck={false}
					aria-describedby={description ? descriptionId : undefined}
					className="pr-10 font-mono"
					{...inputProps}
				/>
				<Button
					type="button"
					variant="ghost"
					size="icon"
					className="absolute top-1/2 right-1 size-7 -translate-y-1/2 text-muted-foreground"
					aria-label={visible ? `Hide ${label}` : `Show ${label}`}
					onClick={() => setVisible((v) => !v)}
				>
					{visible ? <EyeOff /> : <Eye />}
				</Button>
			</div>
			{description && (
				<p id={descriptionId} className="text-muted-foreground text-xs">
					{description}
				</p>
			)}
			{message && <p className="text-destructive text-sm">{message}</p>}
		</div>
	);
}

function SubmitButton({
	children,
	pending,
	disabled,
	className = "w-full",
}: {
	children: ReactNode;
	pending?: boolean;
	disabled?: boolean;
	className?: string;
}) {
	const form = useFormContext();
	return (
		<form.Subscribe selector={(s) => s.isSubmitting}>
			{(isSubmitting) => {
				const busy = pending || isSubmitting;
				return (
					<Button
						type="submit"
						className={className}
						disabled={busy || disabled}
					>
						{busy && <Loader2 className="animate-spin" />}
						{children}
					</Button>
				);
			}}
		</form.Subscribe>
	);
}

export const { useAppForm } = createFormHook({
	fieldContext,
	formContext,
	fieldComponents: { TextField, SecretField },
	formComponents: { SubmitButton },
});

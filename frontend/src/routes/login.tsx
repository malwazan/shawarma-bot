import { createFileRoute, redirect } from "@tanstack/react-router";
import { UtensilsCrossed } from "lucide-react";
import { useState } from "react";
import { LoginForm, RegisterForm } from "#/components/auth/auth-forms";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "#/components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "#/components/ui/toggle-group";
import { sessionQueryOptions } from "#/lib/api/auth";

export const Route = createFileRoute("/login")({
	// The session cookie lives in the browser, so auth checks run client-side only.
	ssr: false,
	beforeLoad: async ({ context }) => {
		const user = await context.queryClient
			.ensureQueryData(sessionQueryOptions)
			.catch(() => null);
		if (user) throw redirect({ to: "/" });
	},
	component: LoginPage,
});

type Mode = "login" | "register";

const COPY: Record<Mode, { title: string; description: string }> = {
	login: {
		title: "Welcome back",
		description: "Log in with your name and password.",
	},
	register: {
		title: "Create an account",
		description: "Pick a name and a password to get started.",
	},
};

function LoginPage() {
	const [mode, setMode] = useState<Mode>("login");

	return (
		<main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-muted/40 p-4">
			<div className="flex items-center gap-2 font-semibold text-lg">
				<span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
					<UtensilsCrossed className="size-5" />
				</span>
				Shawarma Bot
			</div>

			<Card className="w-full max-w-sm">
				<CardHeader className="gap-4">
					<ToggleGroup
						type="single"
						variant="outline"
						className="w-full"
						value={mode}
						// Radix sends "" when the active item is clicked again; keep the current mode.
						onValueChange={(value) => value && setMode(value as Mode)}
					>
						<ToggleGroupItem value="login" className="flex-1">
							Log in
						</ToggleGroupItem>
						<ToggleGroupItem value="register" className="flex-1">
							Register
						</ToggleGroupItem>
					</ToggleGroup>
					<div className="grid gap-1">
						<CardTitle className="text-xl">{COPY[mode].title}</CardTitle>
						<CardDescription>{COPY[mode].description}</CardDescription>
					</div>
				</CardHeader>
				<CardContent>
					{mode === "login" ? <LoginForm /> : <RegisterForm />}
				</CardContent>
			</Card>
		</main>
	);
}

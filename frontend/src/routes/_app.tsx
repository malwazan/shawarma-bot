import {
	createFileRoute,
	Outlet,
	redirect,
	useRouter,
} from "@tanstack/react-router";
import { AppSidebar } from "#/components/app-sidebar";
import { Button } from "#/components/ui/button";
import {
	SidebarInset,
	SidebarProvider,
	SidebarTrigger,
} from "#/components/ui/sidebar";
import { sessionQueryOptions } from "#/lib/api/auth";
import { getErrorMessage, isUnauthorized } from "#/lib/api/client";

/**
 * Layout for every page that needs a logged-in user. Fetches the session
 * (cached by TanStack Query) and redirects to /login when it's missing or expired.
 */
export const Route = createFileRoute("/_app")({
	// The session cookie lives in the browser, so auth checks run client-side only.
	ssr: false,
	beforeLoad: async ({ context }) => {
		try {
			const user =
				await context.queryClient.ensureQueryData(sessionQueryOptions);
			return { user };
		} catch (error) {
			if (isUnauthorized(error)) throw redirect({ to: "/login" });
			throw error;
		}
	},
	component: AppLayout,
	errorComponent: AppError,
});

function AppLayout() {
	return (
		<SidebarProvider>
			<AppSidebar />
			<SidebarInset>
				<header className="flex h-14 items-center gap-2 border-b px-4">
					<SidebarTrigger />
				</header>
				<main className="flex-1 p-4 md:p-6">
					<Outlet />
				</main>
			</SidebarInset>
		</SidebarProvider>
	);
}

/** Anything other than a 401 (e.g. the backend is down). */
function AppError({ error }: { error: unknown }) {
	const router = useRouter();
	return (
		<div className="flex min-h-screen flex-col items-center justify-center gap-4 p-4 text-center">
			<p className="text-muted-foreground">{getErrorMessage(error)}</p>
			<Button variant="outline" onClick={() => router.invalidate()}>
				Try again
			</Button>
		</div>
	);
}

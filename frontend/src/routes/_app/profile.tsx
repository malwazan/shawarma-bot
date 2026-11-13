import { createFileRoute } from "@tanstack/react-router";
import { ApiKeysCard } from "#/components/profile/api-keys-card";
import { FactsCard } from "#/components/profile/facts-card";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "#/components/ui/card";

export const Route = createFileRoute("/_app/profile")({
	component: ProfilePage,
});

function ProfilePage() {
	const { user } = Route.useRouteContext();

	return (
		<div className="mx-auto grid max-w-6xl gap-6">
			<h1 className="font-semibold text-2xl">Profile</h1>
			<Card className="max-w-xl">
				<CardHeader>
					<CardTitle>{user.name}</CardTitle>
					<CardDescription>
						Member since {new Date(user.created_at).toLocaleDateString()}
					</CardDescription>
				</CardHeader>
				<CardContent className="text-muted-foreground text-sm">
					User ID: <span className="font-mono">{user.id}</span>
				</CardContent>
			</Card>
			<ApiKeysCard />
			<FactsCard />
		</div>
	);
}

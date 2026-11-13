import { createFileRoute } from "@tanstack/react-router";
import { CallsTableCard } from "#/components/home/calls-table-card";
import { MakeCallCard } from "#/components/home/make-call-card";

export const Route = createFileRoute("/_app/")({ component: HomePage });

function HomePage() {
	return (
		<div className="mx-auto grid max-w-6xl gap-6">
			<h1 className="font-semibold text-2xl">Home</h1>
			<MakeCallCard />
			<CallsTableCard />
		</div>
	);
}

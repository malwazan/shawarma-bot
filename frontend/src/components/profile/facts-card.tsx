import { useQuery } from "@tanstack/react-query";
import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "#/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "#/components/ui/card";
import { Skeleton } from "#/components/ui/skeleton";
import { getErrorMessage } from "#/lib/api/client";
import { factsQueryOptions, useClearFacts } from "#/lib/api/facts";

/** What the bot remembers about the user, with a way to make it forget. */
export function FactsCard() {
	const { data, isPending, error, refetch } = useQuery(factsQueryOptions);
	const clearFacts = useClearFacts();

	const handleClear = () =>
		clearFacts.mutate(undefined, {
			onSuccess: () => toast.success("The bot has forgotten everything"),
			onError: (err) =>
				toast.error("Couldn't clear the memory", {
					description: getErrorMessage(err),
				}),
		});

	return (
		<Card className="max-w-xl">
			<CardHeader>
				<CardTitle>What the bot remembers</CardTitle>
				<CardDescription>
					After each call, the bot notes facts you shared about yourself, like
					your name or usual order, and uses them in your next calls.
				</CardDescription>
			</CardHeader>
			<CardContent>
				{isPending ? (
					<div className="grid gap-2">
						<Skeleton className="h-4 w-2/3" />
						<Skeleton className="h-4 w-1/2" />
						<Skeleton className="h-4 w-3/5" />
					</div>
				) : error ? (
					<div className="grid justify-items-start gap-3">
						<p className="text-muted-foreground text-sm">
							{getErrorMessage(error)}
						</p>
						<Button variant="outline" size="sm" onClick={() => refetch()}>
							Try again
						</Button>
					</div>
				) : data.facts.length === 0 ? (
					<p className="text-muted-foreground text-sm">
						Nothing yet. Make a call and tell the bot about yourself.
					</p>
				) : (
					<div className="grid gap-4">
						<ul className="grid list-disc gap-1 pl-5 text-sm">
							{data.facts.map((fact) => (
								<li key={fact}>{fact}</li>
							))}
						</ul>
						<div className="flex justify-end">
							<Button
								variant="outline"
								size="sm"
								onClick={handleClear}
								disabled={clearFacts.isPending}
							>
								{clearFacts.isPending ? (
									<Loader2 className="animate-spin" />
								) : (
									<Trash2 />
								)}
								Forget everything
							</Button>
						</div>
					</div>
				)}
			</CardContent>
		</Card>
	);
}

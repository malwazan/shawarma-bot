import { Link } from "@tanstack/react-router";
import { Button } from "#/components/ui/button";

export function NotFound() {
	return (
		<div className="flex min-h-screen flex-col items-center justify-center gap-4 p-4 text-center">
			<p className="font-semibold text-5xl text-primary">404</p>
			<p className="text-muted-foreground">
				The page you're looking for doesn't exist.
			</p>
			<Button asChild variant="outline">
				<Link to="/">Go home</Link>
			</Button>
		</div>
	);
}

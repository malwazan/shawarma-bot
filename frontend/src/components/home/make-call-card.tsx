import { useNavigate } from "@tanstack/react-router";
import { HTTPError } from "ky";
import { Loader2, PhoneOutgoing } from "lucide-react";
import { lazy, Suspense, useCallback, useState } from "react";
import { toast } from "sonner";
import { Button } from "#/components/ui/button";
import { Card, CardContent } from "#/components/ui/card";
import { type CallSession, useMakeCall } from "#/lib/api/calls";
import { getErrorMessage } from "#/lib/api/client";

// WebRTC is browser-only: load LiveKit on the first call, never during SSR.
const CallRoom = lazy(() => import("./call-room"));

/** The API refuses a call with 412 while any of the user's API keys is missing. */
const isMissingApiKeys = (error: unknown) =>
	error instanceof HTTPError && error.response.status === 412;

export function MakeCallCard() {
	const makeCall = useMakeCall();
	const navigate = useNavigate();
	const [session, setSession] = useState<CallSession | null>(null);

	const handleClick = () =>
		makeCall.mutate(undefined, {
			onSuccess: setSession,
			onError: (error) =>
				isMissingApiKeys(error)
					? toast.error("API keys needed", {
							description: getErrorMessage(error),
							action: {
								label: "Open profile",
								onClick: () => navigate({ to: "/profile" }),
							},
						})
					: toast.error("Couldn't start the call", {
							description: getErrorMessage(error),
						}),
		});

	const handleEnded = useCallback(() => {
		setSession(null);
		toast("Call ended");
	}, []);

	return (
		<Card>
			<CardContent className="flex justify-center py-10">
				{session ? (
					<Suspense fallback={<Loader2 className="animate-spin" />}>
						<CallRoom
							key={session.call_id}
							session={session}
							onEnded={handleEnded}
						/>
					</Suspense>
				) : (
					<Button size="lg" onClick={handleClick} disabled={makeCall.isPending}>
						{makeCall.isPending ? (
							<Loader2 className="animate-spin" />
						) : (
							<PhoneOutgoing />
						)}
						Make a Call
					</Button>
				)}
			</CardContent>
		</Card>
	);
}

/**
 * An active call: joins the LiveKit room with the microphone on, plays the
 * bot's audio, and shows the call state with mute / end controls.
 *
 * Browser-only (WebRTC), so `make-call-card` lazy-loads this file: the LiveKit
 * libraries are never loaded during SSR, or before the first call.
 */
import {
	LiveKitRoom,
	RoomAudioRenderer,
	useConnectionState,
	useIsSpeaking,
	useRemoteParticipant,
	useRoomContext,
	useTrackToggle,
} from "@livekit/components-react";
import { ConnectionState, type Participant, Track } from "livekit-client";
import { Mic, MicOff, PhoneOff } from "lucide-react";
import { toast } from "sonner";
import { Button } from "#/components/ui/button";
import type { CallSession } from "#/lib/api/calls";

/** The bot's LiveKit identity; must match AGENT_IDENTITY in backend/src/livekit/service.py. */
const AGENT_IDENTITY = "shawarma-agent";

interface CallRoomProps {
	session: CallSession;
	/** Called once the call is over, whoever ended it. */
	onEnded: () => void;
}

export default function CallRoom({ session, onEnded }: CallRoomProps) {
	return (
		<LiveKitRoom
			serverUrl={session.livekit_url}
			token={session.token}
			connect
			audio
			video={false}
			onDisconnected={onEnded}
			onMediaDeviceFailure={() =>
				toast.error("Microphone unavailable", {
					description: "Allow microphone access to talk to the bot.",
				})
			}
			onError={(error) =>
				toast.error("Call error", { description: error.message })
			}
			className="flex w-full flex-col items-center gap-6"
		>
			<RoomAudioRenderer />
			<CallStatus />
			<CallControls />
		</LiveKitRoom>
	);
}

function CallStatus() {
	const connectionState = useConnectionState();
	const agent = useRemoteParticipant(AGENT_IDENTITY);

	if (connectionState !== ConnectionState.Connected) {
		return <StatusLine pulse>Connecting…</StatusLine>;
	}
	if (!agent) {
		return <StatusLine pulse>Waiting for the bot to join…</StatusLine>;
	}
	return <AgentStatus agent={agent} />;
}

function AgentStatus({ agent }: { agent: Participant }) {
	const speaking = useIsSpeaking(agent);
	return (
		<StatusLine live pulse={speaking}>
			{speaking ? "Bot is speaking" : "Bot is listening"}
		</StatusLine>
	);
}

function StatusLine({
	children,
	live = false,
	pulse = false,
}: {
	children: React.ReactNode;
	live?: boolean;
	pulse?: boolean;
}) {
	return (
		<p
			className="flex items-center gap-2 text-muted-foreground text-sm"
			aria-live="polite"
		>
			<span
				className={`size-2.5 rounded-full ${live ? "bg-emerald-500" : "bg-amber-500"} ${pulse ? "animate-pulse" : ""}`}
			/>
			{children}
		</p>
	);
}

function CallControls() {
	const room = useRoomContext();
	const mic = useTrackToggle({ source: Track.Source.Microphone });

	return (
		<div className="flex gap-3">
			<Button
				variant="outline"
				size="lg"
				onClick={() => mic.toggle()}
				disabled={mic.pending}
				aria-pressed={!mic.enabled}
			>
				{mic.enabled ? <Mic /> : <MicOff />}
				{mic.enabled ? "Mute" : "Unmute"}
			</Button>
			<Button
				variant="destructive"
				size="lg"
				// Leaving fires onDisconnected, which closes the call view.
				onClick={() => room.disconnect()}
			>
				<PhoneOff />
				End call
			</Button>
		</div>
	);
}

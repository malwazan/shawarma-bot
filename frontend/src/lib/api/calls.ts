/** Calls API: start a call, list calls, read a call's transcript. */
import {
	queryOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";
import { http } from "#/lib/api/client";

export type CallStatus = "in_progress" | "completed" | "failed";

export interface Call {
	id: string;
	from_number: string;
	to_number: string;
	/** Seconds; null until the call ends. */
	duration: number | null;
	status: CallStatus;
	started_at: string;
	ended_at: string | null;
}

export type MessageRole = "system" | "user" | "assistant" | "tool";

export interface ToolCall {
	id: string;
	name: string;
	arguments: Record<string, unknown>;
}

export interface CallMessage {
	id: string;
	role: MessageRole;
	content: string | null;
	tool_calls: ToolCall[] | null;
	tool_call_id: string | null;
	tool_name: string | null;
	/** Milliseconds since the call started. */
	timestamp_ms: number;
}

export interface CallDetails extends Call {
	/** API path to stream the recording from; null until the call ends. */
	recording_url: string | null;
	transcript: CallMessage[];
}

/** What the browser needs to join a call's LiveKit room. */
export interface CallSession {
	call_id: string;
	room_name: string;
	token: string;
	livekit_url: string;
}

/** Creates the call (in_progress) and its room. Joining it brings the bot in. */
function makeCall(): Promise<CallSession> {
	return http.post("livekit/calls").json<CallSession>();
}

// While a call is live its row and transcript keep changing: poll until it ends.
const LIVE_REFRESH_MS = 2_000;

// ---------------------------------------------------------------------------
// Queries + mutation
// ---------------------------------------------------------------------------

export const callsQueryOptions = queryOptions({
	queryKey: ["calls"],
	queryFn: () => http.get("calls").json<Call[]>(),
	refetchInterval: (query) =>
		query.state.data?.some((call) => call.status === "in_progress")
			? LIVE_REFRESH_MS
			: false,
});

// The status is in the key, so the details are fetched again once the call
// ends (the recording only exists then).
export const callDetailsQueryOptions = (call: Call) =>
	queryOptions({
		queryKey: ["calls", call.id, call.status],
		queryFn: () => http.get(`calls/${call.id}`).json<CallDetails>(),
		refetchInterval: call.status === "in_progress" ? LIVE_REFRESH_MS : false,
	});

export function useMakeCall() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: makeCall,
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: callsQueryOptions.queryKey }),
	});
}

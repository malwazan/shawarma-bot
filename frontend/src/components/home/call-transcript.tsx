import { useQuery } from "@tanstack/react-query";
import { Wrench } from "lucide-react";
import { Button } from "#/components/ui/button";
import { Skeleton } from "#/components/ui/skeleton";
import {
	type Call,
	type CallMessage,
	callMessagesQueryOptions,
} from "#/lib/api/calls";
import { getErrorMessage } from "#/lib/api/client";

const formatOffset = (ms: number) => {
	const seconds = Math.floor(ms / 1000);
	return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
};

/** A call's transcript; refreshes while the call is in progress. */
export function CallTranscript({ call }: { call: Call }) {
	const { data, isPending, error, refetch } = useQuery(
		callMessagesQueryOptions(call),
	);

	if (isPending) {
		return (
			<div className="grid gap-3">
				{Array.from({ length: 4 }, (_, i) => (
					// biome-ignore lint/suspicious/noArrayIndexKey: static placeholders
					<Skeleton key={i} className="h-12 w-full" />
				))}
			</div>
		);
	}
	if (error) {
		return (
			<div className="text-center text-sm">
				<p className="mb-3 text-muted-foreground">{getErrorMessage(error)}</p>
				<Button variant="outline" size="sm" onClick={() => refetch()}>
					Try again
				</Button>
			</div>
		);
	}

	const messages = data.filter((m) => m.role !== "system");
	const systemPrompt = data.find((m) => m.role === "system")?.content;

	return (
		<div className="grid gap-4">
			{systemPrompt && (
				<details className="rounded-md border p-3 text-sm">
					<summary className="cursor-pointer font-medium text-muted-foreground">
						System prompt
					</summary>
					<p className="mt-2 whitespace-pre-wrap text-muted-foreground">
						{systemPrompt}
					</p>
				</details>
			)}
			{messages.length === 0 ? (
				<p className="text-center text-muted-foreground text-sm">
					{call.status === "in_progress"
						? "Waiting for the conversation to start…"
						: "No messages in this call."}
				</p>
			) : (
				<ol className="grid gap-3">
					{messages.map((message) => (
						<MessageItem key={message.id} message={message} />
					))}
				</ol>
			)}
		</div>
	);
}

function MessageItem({ message }: { message: CallMessage }) {
	const time = (
		<span className="text-muted-foreground text-xs tabular-nums">
			{formatOffset(message.timestamp_ms)}
		</span>
	);

	if (message.role === "assistant" && message.tool_calls?.length) {
		return (
			<li className="flex flex-col gap-1">
				{message.tool_calls.map((call) => (
					<ToolLine key={call.id}>
						Called <code>{call.name}</code>
						{Object.keys(call.arguments).length > 0 && (
							<code className="break-all">
								{" "}
								{JSON.stringify(call.arguments)}
							</code>
						)}
					</ToolLine>
				))}
				{time}
			</li>
		);
	}

	if (message.role === "tool") {
		return (
			<li className="flex flex-col gap-1">
				<ToolLine>
					<code>{message.tool_name}</code> returned{" "}
					<code className="break-all">{message.content}</code>
				</ToolLine>
				{time}
			</li>
		);
	}

	const isUser = message.role === "user";
	return (
		<li
			className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}
		>
			<span className="font-medium text-muted-foreground text-xs">
				{isUser ? "Caller" : "Bot"}
			</span>
			<p
				className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${isUser ? "bg-primary text-primary-foreground" : "bg-muted"}`}
			>
				{message.content}
			</p>
			{time}
		</li>
	);
}

function ToolLine({ children }: { children: React.ReactNode }) {
	return (
		<p className="flex items-start gap-2 rounded-md border border-dashed px-3 py-2 text-muted-foreground text-xs">
			<Wrench className="mt-0.5 size-3 shrink-0" />
			<span>{children}</span>
		</p>
	);
}

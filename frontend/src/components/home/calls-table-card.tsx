import { useQuery } from "@tanstack/react-query";
import {
	createColumnHelper,
	tableFeatures,
	useTable,
} from "@tanstack/react-table";
import { Eye } from "lucide-react";
import { useMemo, useState } from "react";
import { Badge } from "#/components/ui/badge";
import { Button } from "#/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "#/components/ui/card";
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
} from "#/components/ui/sheet";
import { Skeleton } from "#/components/ui/skeleton";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "#/components/ui/table";
import { type Call, type CallStatus, callsQueryOptions } from "#/lib/api/calls";
import { getErrorMessage } from "#/lib/api/client";
import { CallTranscript } from "./call-transcript";

const features = tableFeatures({});
const columnHelper = createColumnHelper<typeof features, Call>();
const EMPTY: Call[] = [];

const dateFormat = new Intl.DateTimeFormat(undefined, {
	dateStyle: "medium",
	timeStyle: "short",
});

const formatDate = (iso: string | null) =>
	iso ? dateFormat.format(new Date(iso)) : "—";

const formatDuration = (seconds: number | null) =>
	seconds === null
		? "—"
		: `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;

const STATUS: Record<CallStatus, { label: string; className: string }> = {
	completed: {
		label: "Completed",
		className:
			"bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
	},
	in_progress: {
		label: "In progress",
		className: "bg-accent text-accent-foreground",
	},
	failed: {
		label: "Failed",
		className: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
	},
};

export function CallsTableCard() {
	const { data, isPending, error, refetch } = useQuery(callsQueryOptions);
	// Track the id, not the row: polling replaces the rows while a call is live.
	const [selectedId, setSelectedId] = useState<string | null>(null);
	const selected = data?.find((call) => call.id === selectedId) ?? null;

	const columns = useMemo(
		() =>
			columnHelper.columns([
				columnHelper.accessor("id", {
					header: "ID",
					cell: (info) => (
						<span className="font-mono text-xs" title={info.getValue()}>
							{info.getValue().slice(0, 8)}
						</span>
					),
				}),
				columnHelper.accessor("from_number", { header: "From" }),
				columnHelper.accessor("to_number", { header: "To" }),
				columnHelper.accessor("duration", {
					header: "Duration",
					cell: (info) => (
						<span className="tabular-nums">
							{formatDuration(info.getValue())}
						</span>
					),
				}),
				columnHelper.accessor("started_at", {
					header: "Started At",
					cell: (info) => formatDate(info.getValue()),
				}),
				columnHelper.accessor("ended_at", {
					header: "Ended At",
					cell: (info) => formatDate(info.getValue()),
				}),
				columnHelper.accessor("status", {
					header: "Status",
					cell: (info) => {
						const status = STATUS[info.getValue()];
						return (
							<Badge variant="secondary" className={status.className}>
								{status.label}
							</Badge>
						);
					},
				}),
				columnHelper.display({
					id: "view",
					header: () => <span className="sr-only">View</span>,
					cell: ({ row }) => (
						<Button
							variant="ghost"
							size="icon"
							aria-label={`View call ${row.original.id}`}
							onClick={() => setSelectedId(row.original.id)}
						>
							<Eye />
						</Button>
					),
				}),
			]),
		[],
	);

	const table = useTable({ features, columns, data: data ?? EMPTY });

	return (
		<Card>
			<CardHeader>
				<CardTitle>Recent calls</CardTitle>
				<CardDescription>
					Your latest calls. Live calls update as they happen.
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Table>
					<TableHeader>
						{table.getHeaderGroups().map((headerGroup) => (
							<TableRow key={headerGroup.id}>
								{headerGroup.headers.map((header) => (
									<TableHead key={header.id}>
										<table.FlexRender header={header} />
									</TableHead>
								))}
							</TableRow>
						))}
					</TableHeader>
					<TableBody>
						{isPending ? (
							Array.from({ length: 5 }, (_, i) => (
								// biome-ignore lint/suspicious/noArrayIndexKey: static placeholders
								<TableRow key={i}>
									<TableCell colSpan={columns.length}>
										<Skeleton className="h-6 w-full" />
									</TableCell>
								</TableRow>
							))
						) : error ? (
							<TableRow>
								<TableCell
									colSpan={columns.length}
									className="py-10 text-center"
								>
									<p className="mb-3 text-muted-foreground">
										{getErrorMessage(error)}
									</p>
									<Button variant="outline" size="sm" onClick={() => refetch()}>
										Try again
									</Button>
								</TableCell>
							</TableRow>
						) : table.getRowModel().rows.length === 0 ? (
							<TableRow>
								<TableCell
									colSpan={columns.length}
									className="py-10 text-center text-muted-foreground"
								>
									No calls yet.
								</TableCell>
							</TableRow>
						) : (
							table.getRowModel().rows.map((row) => (
								<TableRow key={row.id}>
									{row.getAllCells().map((cell) => (
										<TableCell key={cell.id}>
											<table.FlexRender cell={cell} />
										</TableCell>
									))}
								</TableRow>
							))
						)}
					</TableBody>
				</Table>
			</CardContent>

			<Sheet
				open={selected !== null}
				onOpenChange={(open) => !open && setSelectedId(null)}
			>
				<SheetContent className="w-full overflow-y-auto sm:max-w-lg">
					<SheetHeader>
						<SheetTitle>Call transcript</SheetTitle>
						<SheetDescription>
							{selected &&
								`${formatDate(selected.started_at)} · ${STATUS[selected.status].label} · ${formatDuration(selected.duration)}`}
						</SheetDescription>
					</SheetHeader>
					<div className="px-4 pb-6">
						{selected && <CallTranscript call={selected} />}
					</div>
				</SheetContent>
			</Sheet>
		</Card>
	);
}

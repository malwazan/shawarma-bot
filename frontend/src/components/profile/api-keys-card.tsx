import { useQuery } from "@tanstack/react-query";
import { CircleAlert, CircleCheck } from "lucide-react";
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
import {
	type ApiKeyName,
	type ApiKeys,
	type ApiKeysUpdate,
	apiKeysQueryOptions,
	useUpdateApiKeys,
} from "#/lib/api/api-keys";
import { getErrorMessage } from "#/lib/api/client";
import { useAppForm } from "#/lib/form";

// Keep the models in sync with backend/src/voice/providers.py.
const FIELDS: Array<{
	name: ApiKeyName;
	label: string;
	description: string;
}> = [
	{
		name: "llm_key",
		label: "LLM (Google Gemini)",
		description:
			"A Google AI Studio API key (aistudio.google.com/apikey) with access to the gemini-3.6-flash model.",
	},
	{
		name: "stt_key",
		label: "Speech to Text (ElevenLabs)",
		description:
			"An ElevenLabs API key with the Speech to Text permission, for the scribe_v2_realtime model.",
	},
	{
		name: "tts_key",
		label: "Text to Speech (ElevenLabs)",
		description:
			"An ElevenLabs API key with the Text to Speech permission, for the eleven_turbo_v2_5 model. The same key as Speech to Text works if it has both permissions.",
	},
];

const EMPTY = { llm_key: "", stt_key: "", tts_key: "" };

export function ApiKeysCard() {
	const { data, isPending, error, refetch } = useQuery(apiKeysQueryOptions);

	return (
		<Card className="max-w-xl">
			<CardHeader>
				<CardTitle>API Keys</CardTitle>
				<CardDescription>
					Your bot runs on your own keys, and all three are needed to make a
					call. Saved keys are stored encrypted and are never shown again.
				</CardDescription>
			</CardHeader>
			<CardContent>
				{isPending ? (
					<div className="grid gap-5">
						{FIELDS.map((f) => (
							<div key={f.name} className="grid gap-2">
								<Skeleton className="h-4 w-40" />
								<Skeleton className="h-9 w-full" />
							</div>
						))}
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
				) : (
					<ApiKeysForm saved={data} />
				)}
			</CardContent>
		</Card>
	);
}

/**
 * Inputs start empty: type a key to set or replace it. Keys left empty keep
 * their saved value.
 */
function ApiKeysForm({ saved }: { saved: ApiKeys }) {
	const updateKeys = useUpdateApiKeys();

	const form = useAppForm({
		defaultValues: EMPTY,
		onSubmit: async ({ value }) => {
			const changes: ApiKeysUpdate = {};
			for (const { name } of FIELDS) {
				const key = value[name].trim();
				if (key) changes[name] = key;
			}
			try {
				await updateKeys.mutateAsync(changes);
				form.reset(EMPTY);
				toast.success("API keys saved");
			} catch (err) {
				toast.error("Couldn't save API keys", {
					description: getErrorMessage(err),
				});
			}
		},
	});

	return (
		<form
			noValidate
			className="grid gap-5"
			onSubmit={(e) => {
				e.preventDefault();
				form.handleSubmit();
			}}
		>
			{FIELDS.map(({ name, label, description }) => (
				<form.AppField key={name} name={name}>
					{(field) => (
						<field.SecretField
							label={label}
							description={description}
							status={<KeyStatus masked={saved[name]} />}
							placeholder={
								saved[name] ? "Enter a new key to replace it" : "Enter key"
							}
						/>
					)}
				</form.AppField>
			))}

			<form.Subscribe
				selector={(s) => FIELDS.some((f) => s.values[f.name].trim())}
			>
				{(anyFilled) => (
					<div className="flex justify-end">
						<form.AppForm>
							<form.SubmitButton className="" disabled={!anyFilled}>
								Save
							</form.SubmitButton>
						</form.AppForm>
					</div>
				)}
			</form.Subscribe>
		</form>
	);
}

function KeyStatus({ masked }: { masked: string | null }) {
	return masked ? (
		<span className="flex items-center gap-1 text-emerald-700 text-xs dark:text-emerald-400">
			<CircleCheck className="size-3.5" />
			Saved <span className="font-mono">{masked}</span>
		</span>
	) : (
		<span className="flex items-center gap-1 text-amber-700 text-xs dark:text-amber-400">
			<CircleAlert className="size-3.5" />
			Not set
		</span>
	);
}

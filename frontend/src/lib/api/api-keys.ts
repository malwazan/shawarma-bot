/**
 * The user's own API keys for the voice bot. Saved keys never come back from
 * the server: it returns a masked hint ("••••abcd") or null if not set.
 */
import {
	queryOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";
import { http } from "#/lib/api/client";

export type ApiKeyName = "llm_key" | "stt_key" | "tts_key";

/** Masked saved keys; null = not set. */
export type ApiKeys = Record<ApiKeyName, string | null>;

/** Keys to set; leave one out to keep its saved value. */
export type ApiKeysUpdate = Partial<Record<ApiKeyName, string>>;

export const apiKeysQueryOptions = queryOptions({
	queryKey: ["api-keys"],
	queryFn: () => http.get("users/api-keys").json<ApiKeys>(),
});

export function useUpdateApiKeys() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: (keys: ApiKeysUpdate) =>
			http.put("users/api-keys", { json: keys }).json<ApiKeys>(),
		onSuccess: (keys) =>
			queryClient.setQueryData(apiKeysQueryOptions.queryKey, keys),
	});
}

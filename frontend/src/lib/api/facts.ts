/** What the bot remembers about the user, learned from their calls. */
import {
	queryOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";
import { http } from "#/lib/api/client";

export interface Facts {
	facts: string[];
}

export const factsQueryOptions = queryOptions({
	queryKey: ["facts"],
	queryFn: () => http.get("users/facts").json<Facts>(),
});

export function useClearFacts() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: () => http.delete("users/facts"),
		onSuccess: () =>
			queryClient.setQueryData(factsQueryOptions.queryKey, { facts: [] }),
	});
}

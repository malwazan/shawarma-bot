import {
	queryOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";
import { http } from "./client";

export interface User {
	id: string;
	name: string;
	created_at: string;
}

export interface Credentials {
	name: string;
	password: string;
}

// ---------------------------------------------------------------------------
// API calls (backend/src/user/endpoints.py)
// ---------------------------------------------------------------------------

const getSession = () => http.get("users/session").json<User>();

const login = (body: Credentials) =>
	http.post("users/login", { json: body }).json<User>();

const register = (body: Credentials) =>
	http.post("users/register", { json: body }).json<User>();

const logout = async () => {
	await http.post("users/logout");
};

// ---------------------------------------------------------------------------
// Query + mutations
// ---------------------------------------------------------------------------

export const sessionQueryOptions = queryOptions({
	queryKey: ["session"],
	queryFn: getSession,
	staleTime: 5 * 60 * 1000,
	retry: false,
});

/** Login and register both return the user and set the cookie, so the session
 * cache is filled directly instead of refetching it. */
function useAuthMutation(mutationFn: (body: Credentials) => Promise<User>) {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn,
		onSuccess: (user) => {
			queryClient.setQueryData(sessionQueryOptions.queryKey, user);
		},
	});
}

export const useLogin = () => useAuthMutation(login);
export const useRegister = () => useAuthMutation(register);

export function useLogout() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: logout,
		// Drop every cached query so nothing from this user survives the logout.
		onSuccess: () => queryClient.removeQueries(),
	});
}

import ky, { HTTPError } from "ky";

/**
 * Shared HTTP client. The API is served from the same origin as the frontend
 * (Caddy in production, the Vite dev proxy locally), so relative URLs work and the
 * browser sends the session cookie automatically.
 */
export const http = ky.create({
	baseUrl: "/api/v1/",
	timeout: 30_000,
	retry: 0,
});

/** FastAPI error bodies: `{"detail": "msg"}` or, for 422, `{"detail": [{loc, msg}]}`. */
interface FastApiErrorBody {
	detail?: string | Array<{ loc: Array<string | number>; msg: string }>;
}

export function isUnauthorized(error: unknown): boolean {
	return error instanceof HTTPError && error.response.status === 401;
}

/** A human-readable message for any error thrown by an API call. */
export function getErrorMessage(error: unknown): string {
	if (error instanceof HTTPError) {
		const { detail } = (error.data ?? {}) as FastApiErrorBody;
		if (typeof detail === "string") return detail;
		if (Array.isArray(detail) && detail.length > 0) return detail[0].msg;
		return `Request failed (${error.response.status})`;
	}
	if (error instanceof TypeError) {
		return "Can't reach the server. Check your connection and try again.";
	}
	return error instanceof Error ? error.message : "Something went wrong";
}

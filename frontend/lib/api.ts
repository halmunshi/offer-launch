const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  throw new Error("NEXT_PUBLIC_API_URL is not set");
}

async function request<T>(input: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${input}`, init);

  if (!response.ok) {
    let detail = "";

    try {
      const payload = (await response.json()) as { detail?: string };
      detail = typeof payload.detail === "string" ? payload.detail : "";
    } catch {
      detail = await response.text();
    }

    if (response.status === 401 && typeof window !== "undefined") {
      const redirect = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.href = `/sign-in?redirect_url=${redirect}`;
    }

    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function buildAuthHeader(token: string | null): Record<string, string> {
  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

export const api = {
  get: async <T>(path: string, token: string | null): Promise<T> => {
    return request<T>(path, {
      method: "GET",
      headers: buildAuthHeader(token),
      cache: "no-store",
    });
  },

  post: async <T, B>(path: string, body: B, token: string | null): Promise<T> => {
    return request<T>(path, {
      method: "POST",
      headers: {
        ...buildAuthHeader(token),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  },

  patch: async <T, B>(path: string, body: B, token: string | null): Promise<T> => {
    return request<T>(path, {
      method: "PATCH",
      headers: {
        ...buildAuthHeader(token),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  },

  put: async <T, B>(path: string, body: B, token: string | null): Promise<T> => {
    return request<T>(path, {
      method: "PUT",
      headers: {
        ...buildAuthHeader(token),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  },

  del: async <T>(path: string, token: string | null): Promise<T> => {
    return request<T>(path, {
      method: "DELETE",
      headers: buildAuthHeader(token),
      cache: "no-store",
    });
  },

  upload: async <T>(path: string, formData: FormData, token: string | null): Promise<T> => {
    return request<T>(path, {
      method: "POST",
      headers: buildAuthHeader(token),
      body: formData,
      cache: "no-store",
    });
  },
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  throw new Error("NEXT_PUBLIC_API_URL is not set");
}

async function request<T>(input: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${input}`, init);

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(errorBody || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export const api = {
  get: async <T>(path: string, token: string): Promise<T> => {
    return request<T>(path, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });
  },

  post: async <T, B>(path: string, body: B, token: string): Promise<T> => {
    return request<T>(path, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  },
};

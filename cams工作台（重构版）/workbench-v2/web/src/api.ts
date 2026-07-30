const API_ROOT = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://127.0.0.1:8013" : "");

export type User = { id: number; username: string; role: string };

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("cams_token");
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_ROOT}${path}`, { ...init, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail || "请求失败");
  }
  return response.json() as Promise<T>;
}

export async function login(username: string, password: string): Promise<User> {
  const payload = await api<{ access_token: string; user: User }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  localStorage.setItem("cams_token", payload.access_token);
  return payload.user;
}

export async function openApiResource(path: string, filename?: string): Promise<void> {
  const token = localStorage.getItem("cams_token");
  const response = await fetch(`${API_ROOT}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error("文件读取失败");
  const url = URL.createObjectURL(await response.blob());
  if (filename) {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
  } else {
    window.open(url, "_blank", "noopener,noreferrer");
  }
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

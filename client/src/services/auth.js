async function read(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Request failed. Please try again.');
  return data;
}

async function post(path, body) {
  const {csrfToken} = await read(await fetch('/api/auth/csrf/', {credentials: 'same-origin'}));
  return read(await fetch(path, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      ...(body instanceof FormData ? {} : {'Content-Type': 'application/json'}),
      'X-CSRFToken': csrfToken,
    },
    body: body instanceof FormData ? body : JSON.stringify(body),
  }));
}

export function login(identifier, password) {
  return post('/api/auth/login/', {identifier, password});
}

export function register(details) {
  return post('/api/auth/register/', details);
}

export function logout() {
  return post('/api/auth/logout/', {});
}

export async function currentUser() {
  const response = await fetch('/api/auth/me/', {credentials: 'same-origin'});
  if (response.status === 401) return null;
  return (await read(response)).user;
}

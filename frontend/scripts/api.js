const API_BASE = 'https://wish-apps.onrender.com';  // not localhost? Use 127.0.0.1

let authToken = null;

export function setAuthToken(token) {
    authToken = token;
    localStorage.setItem('wishbridge_token', token);
}

export function getAuthToken() {
    if (!authToken) {
        authToken = localStorage.getItem('wishbridge_token');
    }
    return authToken;
}

export function clearAuthToken() {
    authToken = null;
    localStorage.removeItem('wishbridge_token');
}

async function request(endpoint, method, body = null) {
    const headers = {
        'Content-Type': 'application/json',
    };
    const token = getAuthToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const options = { method, headers };
    if (body) {
        options.body = JSON.stringify(body);
    }
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    if (response.status === 401) {
        clearAuthToken();
        window.location.href = '/login.html';  // redirect if unauthenticated
    }
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
    }
    return data;
}

// Auth
export async function signup(username, email, password) {
    return request('/users/signup', 'POST', { username, email, password });
}

export async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const response = await fetch(`${API_BASE}/users/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail);
    setAuthToken(data.access_token);
    return data;
}

// Wishes
export async function createWish(wishData) {
    return request('/wishes/', 'POST', wishData);
}

export async function getRandomWish() {
    return request('/wishes/random', 'GET');
}

// Grants
export async function grantWish(wishId, granterNote = '') {
    return request('/grants/', 'POST', { wish_id: wishId, note: granterNote });
}

// Reports
export async function reportWish(wishId, reason) {
    return request('/reports/', 'POST', { wish_id: wishId, reason });
}

// User profile
export async function getMe() {
    return request('/users/me', 'GET');
}
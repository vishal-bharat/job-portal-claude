import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, setSession, getUser } from '../api/client.js';

export default function Login() {
  const nav = useNavigate();
  if (getUser()) { nav('/', { replace: true }); }

  const [email, setEmail] = useState('alex@gisma.edu');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.login(email, password);
      setSession(res.token, { email: res.email, name: res.name });
      nav('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <div className="brand-logo" style={{ marginBottom: 16 }}>G</div>
        <h1>Career Connect</h1>
        <p>Sign in to find opportunities matched to your skills.</p>

        {error && <div className="error">{error}</div>}

        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />

        <label>Password</label>
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />

        <button className="btn-primary" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign in'}
        </button>

        <div className="hint">Demo: <b>alex@gisma.edu</b> / <b>password123</b></div>
      </form>
    </div>
  );
}

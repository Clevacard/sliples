export default function CliSuccess() {
  return (
    <div style={{ padding: '3rem', textAlign: 'center', fontFamily: 'sans-serif', color: '#e5e7eb', background: '#111827', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✓</div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.5rem' }}>Authentication successful</h2>
      <p style={{ color: '#9ca3af' }}>You can close this tab and return to your terminal.</p>
    </div>
  )
}

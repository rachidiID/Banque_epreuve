const TestPage = () => {
  return (
    <div style={{ padding: '20px', background: 'white' }}>
      <h1 style={{ color: 'red', fontSize: '48px' }}>PAGE DE TEST</h1>
      <p>Si vous voyez ce texte, React fonctionne !</p>
      <ul>
        <li>Navigateur : {navigator.userAgent}</li>
        <li>URL actuelle : {window.location.href}</li>
        <li>Date : {new Date().toLocaleString()}</li>
      </ul>
    </div>
  )
}

export default TestPage

import React from 'react';
import PlantDetails from './components/PlantDetails';
import './components/global.css';
import './App.css';

function App() {
  // Chỉ có 1 plant duy nhất
  const plantId = process.env.REACT_APP_PLANT_ID || 'plant_001';

  return (
    <div className="App">
      <header className="App-header">
        <h1>🌱 Gardenice Plant Monitor</h1>
        <p className="subtitle">Real-time monitoring system</p>
      </header>
      <main>
        <PlantDetails plantId={plantId} />
      </main>
      <footer className="App-footer">
        <p>Gardernice - Monitor your garden in a effective way</p>
      </footer>
    </div>
  );
}

export default App;

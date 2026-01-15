import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ParablesList from './components/ParablesList'
import ParableDetail from './components/ParableDetail'
import CreateParable from './components/CreateParable'

function App() {
  return (
    <Router>
      <div className="container">
        <header className="header">
          <h1>🎬 Content Creator</h1>
          <p>Автоматическая генерация YouTube Shorts из притч</p>
        </header>
        
        <Routes>
          <Route path="/" element={<ParablesList />} />
          <Route path="/create" element={<CreateParable />} />
          <Route path="/parable/:id" element={<ParableDetail />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App


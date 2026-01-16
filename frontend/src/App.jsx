import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ParablesList from './components/ParablesList'
import ParableDetail from './components/ParableDetail'
import CreateParable from './components/CreateParable'
import EnglishParableDetail from './components/EnglishParableDetail'

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
          <Route path="/parable/:id/english" element={<EnglishParableDetail />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App


import { useState } from 'react'
import TaskCreator from './components/TaskCreator'
import TaskList from './components/TaskList'
import './App.css'

function App() {
  const [refresh, setRefresh] = useState(0)

  const handleTaskCreated = () => {
    setRefresh(prev => prev + 1)
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-6 shadow-lg">
        <h1 className="text-3xl font-bold">Browser Automation System</h1>
        <p className="mt-2 text-blue-100">
          Самообучающаяся система автоматизации браузера
        </p>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <TaskCreator onTaskCreated={handleTaskCreated} />
          </div>
          
          <div className="lg:col-span-2">
            <TaskList key={refresh} />
          </div>
        </div>
      </main>
    </div>
  )
}

export default App

import { useState, useEffect } from 'react'
import axios from 'axios'

interface Task {
  task_id: string
  mini_prompt: string
  status: string
  created_at: string
  executions_count: number
  last_execution: any
}

export default function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTasks()
  }, [])

  const fetchTasks = async () => {
    try {
      const response = await axios.get('/api/tasks/')
      setTasks(response.data.tasks)
    } catch (err) {
      console.error('Error loading tasks:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      in_progress: 'bg-blue-100 text-blue-800',
      pending: 'bg-gray-100 text-gray-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      completed: 'Выполнено',
      failed: 'Ошибка',
      in_progress: 'Выполняется',
      pending: 'Ожидает'
    }
    return texts[status] || status
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h2 className="text-2xl font-bold">История задач</h2>
      </div>
      
      {tasks.length === 0 ? (
        <div className="p-6 text-center text-gray-500">
          Пока нет выполненных задач
        </div>
      ) : (
        <div className="divide-y">
          {tasks.map((task) => (
            <div key={task.task_id} className="p-6 hover:bg-gray-50">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-medium text-lg">{task.mini_prompt}</h3>
                <span className={'px-3 py-1 rounded-full text-xs font-semibold ' + getStatusColor(task.status)}>
                  {getStatusText(task.status)}
                </span>
              </div>
              
              <div className="text-sm text-gray-600 space-y-1">
                <p>ID: {task.task_id}</p>
                <p>Создано: {new Date(task.created_at).toLocaleString('ru-RU')}</p>
                <p>Выполнений: {task.executions_count}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

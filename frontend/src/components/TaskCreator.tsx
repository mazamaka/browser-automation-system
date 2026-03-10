import { useState } from 'react'
import axios from 'axios'

interface TaskCreatorProps {
  onTaskCreated: () => void
}

export default function TaskCreator({ onTaskCreated }: TaskCreatorProps) {
  const [miniPrompt, setMiniPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!miniPrompt.trim()) {
      setError('Введите промпт')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await axios.post('/api/tasks/create', {
        mini_prompt: miniPrompt,
        metadata: {}
      })

      setSuccess('Задача создана успешно!')
      setMiniPrompt('')
      onTaskCreated()

      // Автоматически запускаем выполнение
      setTimeout(async () => {
        try {
          await axios.post(`/api/tasks/${response.data.task_id}/run`, {
            force_new_prompt: false
          })
        } catch (err) {
          console.error('Ошибка запуска:', err)
        }
      }, 500)

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка создания задачи')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-4">Создать задачу</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Мини-промпт
          </label>
          <textarea
            value={miniPrompt}
            onChange={(e) => setMiniPrompt(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={5}
            placeholder="Например: зайти в гугл аккаунт и запустить рекламу по пиву"
            disabled={loading}
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
            {success}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {loading ? 'Создание...' : 'Создать и запустить'}
        </button>
      </form>

      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">Как это работает?</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Введите короткое описание задачи</li>
          <li>• Система откроет браузер и проанализирует страницу</li>
          <li>• AI создаст детальный план действий</li>
          <li>• Browser-use выполнит задачу автоматически</li>
          <li>• Результаты будут сохранены для обучения</li>
        </ul>
      </div>
    </div>
  )
}

import { useState, useRef, useEffect } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8003'

console.log('🔍 API_BASE_URL:', API_BASE_URL)
console.log('🔍 VITE_API_URL:', import.meta.env.VITE_API_URL)
console.log('🔍 NODE_ENV:', import.meta.env.NODE_ENV)
console.log('🔍 MODE:', import.meta.env.MODE)

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message to UI
    const newUserMessage = { type: 'user', content: userMessage }
    setMessages(prev => [...prev, newUserMessage])

    try {
      console.log('📡 Making API call to:', `${API_BASE_URL}/chat`)
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      })

      console.log('📡 Response status:', response.status)
      console.log('📡 Response ok:', response.ok)

      if (!response.ok) {
        const errorText = await response.text()
        console.log('📡 Error response:', errorText)
        throw new Error(`Failed to send message: ${response.status} ${errorText}`)
      }

      const data = await response.json()
      console.log('📡 Success response:', data)

      // Update session ID if we got a new one
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id)
      }

      // Add AI response to UI
      const aiMessage = { type: 'ai', content: data.response }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        type: 'ai',
        content: 'Sorry, I encountered an error. Please try again.',
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const resetChat = async () => {
    if (!sessionId) {
      // If no session, just clear local state
      setMessages([])
      setInput('')
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setSessionId(data.session_id)
        setMessages([])
        setInput('')
      }
    } catch (error) {
      console.error('Error resetting chat:', error)
      // Still clear local state even if API call fails
      setMessages([])
      setInput('')
      setSessionId(null)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>👋 Welcome! I'm here to help you with:</p>
            <ul>
              <li>📚 General education guidance</li>
              <li>🎓 Career & degree guidance</li>
              <li>💚 Mental health & academic stress support</li>
            </ul>
            <p>Feel free to ask me anything about your educational journey!</p>
          </div>
        )}
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message ai">
            <div className="message-content">
              <span className="typing-indicator">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here..."
            disabled={loading}
            className="chat-input"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="send-button"
          >
            Send
          </button>
        </div>
        <button
          onClick={resetChat}
          className="reset-button"
          title="Reset Chat"
        >
          🔄 Reset Chat
        </button>
      </div>
    </div>
  )
}

export default Chat







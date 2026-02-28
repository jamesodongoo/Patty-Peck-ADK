/**
 * ChatMessage - Individual message display component
 * Bubble icon = AI persona avatar for each message from our AI
 */
import ProductCarousel from './ProductCarousel'
import HondaLogo from '../assets/logo-honda.png'
import UserLogo from '../assets/UserLogo.jpg'

function MessageContent({ text }) {
  if (!text) return null

  // Process markdown-style formatting
  const renderLine = (line, lineIndex) => {
    // Handle bold **text**
    const parts = line.split(/(\*\*[^*]+\*\*)/g)
    
    return (
      <p key={lineIndex} className="message-line">
        {parts.map((part, i) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={i}>{part.slice(2, -2)}</strong>
          }
          // Handle URLs
          const urlRegex = /(https?:\/\/[^\s<>"{}|\\^`[\]]+)/g
          const segments = part.split(urlRegex)
          return segments.map((seg, j) => {
            if (seg.match(/^https?:\/\//)) {
              return (
                <a 
                  key={`${i}-${j}`}
                  href={seg}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="message-link"
                >
                  {seg.length > 50 ? seg.slice(0, 50) + '...' : seg}
                </a>
              )
            }
            return <span key={`${i}-${j}`}>{seg}</span>
          })
        })}
      </p>
    )
  }

  return (
    <div className="message-content">
      {text.split('\n').map((line, index) => renderLine(line, index))}
    </div>
  )
}

export function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  const hasProducts = message.products && message.products.length > 0

  return (
    <div className={`chat-message ${isUser ? 'chat-message-user' : ''} ${isSystem ? 'chat-message-system' : ''}`}>
      {/* Avatar: user logo, Honda brand for system/AI */}
      <div className={`message-avatar ${isUser ? 'avatar-user' : isSystem ? 'avatar-system' : 'avatar-agent'}`}>
        {isUser ? (
          <img src={UserLogo} alt="" aria-hidden />
        ) : (
          <img src={HondaLogo} alt="" aria-hidden />
        )}
      </div>

      {/* Message Content */}
      <div className="message-body">
        <div className={`message-bubble ${isUser ? 'bubble-user' : isSystem ? 'bubble-system' : 'bubble-agent'}`}>
          {/* Always show AI text (may include color/features summary) */}
          <MessageContent text={message.text} />

          {/* Products carousel - shown below text when products exist */}
          {hasProducts && (
            <ProductCarousel products={message.products} />
          )}
        </div>

      </div>
    </div>
  )
}

export default ChatMessage


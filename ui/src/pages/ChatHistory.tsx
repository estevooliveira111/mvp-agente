import { useEffect, useState, type FormEvent } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { Bot, Loader2, MessageSquare, Search, User as UserIcon } from 'lucide-react'
import { fetchChatMessages, fetchChatSessions, type ChatMessage, type ChatSessionSummary } from '@/api/chat'

const STORAGE_KEY = 'chat_external_id'

export default function ChatHistory() {
  const [externalId, setExternalId] = useState(() => localStorage.getItem(STORAGE_KEY) || '')
  const [searchInput, setSearchInput] = useState(externalId)
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)

  const sessionsQuery = useQuery({
    queryKey: ['chat-sessions', externalId],
    queryFn: () => fetchChatSessions(externalId),
    enabled: !!externalId,
  })

  const messagesQuery = useQuery({
    queryKey: ['chat-messages', selectedSessionId],
    queryFn: () => fetchChatMessages(selectedSessionId as string),
    enabled: !!selectedSessionId,
  })

  useEffect(() => {
    if (sessionsQuery.data && sessionsQuery.data.length > 0 && !selectedSessionId) {
      setSelectedSessionId(sessionsQuery.data[0].session_id)
    }
  }, [sessionsQuery.data, selectedSessionId])

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = searchInput.trim()
    localStorage.setItem(STORAGE_KEY, trimmed)
    setSelectedSessionId(null)
    setExternalId(trimmed)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Conversas</h2>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 max-w-md">
        <div className="relative flex-1">
          <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="ID do usuário (ex: número do Telegram)"
            className="w-full pl-9 pr-4 py-2 bg-background border border-border rounded-md text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <button
          type="submit"
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          Buscar
        </button>
      </form>

      {!externalId && (
        <div className="p-10 text-center text-muted-foreground bg-card border border-border rounded-xl">
          Informe o ID do usuário acima para carregar o histórico de conversas.
        </div>
      )}

      {externalId && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-[600px]">
          <div className="bg-card border border-border rounded-xl overflow-hidden flex flex-col">
            <div className="p-4 border-b border-border">
              <h3 className="font-semibold text-foreground">Sessões</h3>
            </div>
            <div className="flex-1 overflow-y-auto">
              {sessionsQuery.isLoading && (
                <div className="p-6 flex justify-center text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              )}
              {sessionsQuery.isError && (
                <div className="p-6 text-sm text-destructive">
                  Não foi possível carregar as conversas.
                </div>
              )}
              {sessionsQuery.data?.length === 0 && (
                <div className="p-6 text-sm text-muted-foreground">
                  Nenhuma conversa encontrada para este usuário.
                </div>
              )}
              {sessionsQuery.data?.map((session) => (
                <SessionListItem
                  key={session.session_id}
                  session={session}
                  active={session.session_id === selectedSessionId}
                  onClick={() => setSelectedSessionId(session.session_id)}
                />
              ))}
            </div>
          </div>

          <div className="md:col-span-2 bg-card border border-border rounded-xl overflow-hidden flex flex-col">
            <div className="p-4 border-b border-border">
              <h3 className="font-semibold text-foreground">
                {selectedSessionId ? `Sessão ${selectedSessionId}` : 'Selecione uma conversa'}
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {!selectedSessionId && (
                <div className="h-full flex items-center justify-center text-muted-foreground text-sm gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Escolha uma conversa na lista ao lado.
                </div>
              )}
              {messagesQuery.isLoading && (
                <div className="flex justify-center text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              )}
              {messagesQuery.data?.map((message) => (
                <ChatBubble key={message.id} message={message} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function SessionListItem({
  session,
  active,
  onClick,
}: {
  session: ChatSessionSummary
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 border-b border-border transition-colors ${
        active ? 'bg-primary/10' : 'hover:bg-muted'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium text-foreground truncate">
          Sessão {session.session_id}
        </span>
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {formatDistanceToNow(new Date(session.last_message_at), { addSuffix: true, locale: ptBR })}
        </span>
      </div>
      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
        {session.last_message_preview || 'Sem mensagens'}
      </p>
      <p className="text-xs text-muted-foreground mt-1">{session.message_count} mensagens</p>
    </button>
  )
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        <p className={`text-[10px] mt-1 ${isUser ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
          {format(new Date(message.created_at), 'dd/MM HH:mm')}
        </p>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0">
          <UserIcon className="h-4 w-4 text-muted-foreground" />
        </div>
      )}
    </div>
  )
}

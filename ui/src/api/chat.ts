import api from '@/lib/axios'

export interface ChatSessionSummary {
  id: number
  session_id: string
  created_at: string
  last_message_at: string
  last_message_preview: string
  message_count: number
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  created_at: string
}

export async function fetchChatSessions(externalId: string): Promise<ChatSessionSummary[]> {
  const { data } = await api.get<ChatSessionSummary[]>('/chat/sessions', {
    params: { external_id: externalId },
  })
  return data
}

export async function fetchChatMessages(sessionId: string): Promise<ChatMessage[]> {
  const { data } = await api.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`)
  return data
}

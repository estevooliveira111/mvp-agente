import { useState, type FormEvent } from 'react'

const STORAGE_KEY = 'chat_external_id'

/**
 * Identifica "quem é o usuário" enquanto não existe login real ligado ao
 * external_id do canal (hoje, o ID do Telegram). Compartilhado entre as
 * telas de Conversas e Agenda para que a busca feita em uma valha na outra.
 */
export function useExternalId() {
  const [externalId, setExternalId] = useState(() => localStorage.getItem(STORAGE_KEY) || '')
  const [searchInput, setSearchInput] = useState(externalId)

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = searchInput.trim()
    localStorage.setItem(STORAGE_KEY, trimmed)
    setExternalId(trimmed)
  }

  return { externalId, searchInput, setSearchInput, handleSearch }
}

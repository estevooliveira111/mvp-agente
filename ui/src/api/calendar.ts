import api from '@/lib/axios'

export type EventPriority = 'low' | 'medium' | 'high'
export type EventStatus = 'scheduled' | 'cancelled' | 'completed'
export type RepeatOption = 'none' | 'daily' | 'weekly' | 'monthly'

export interface CalendarEvent {
  id: number
  title: string
  description: string | null
  category: string | null
  start_time: string
  end_time: string
  location: string | null
  meeting_link: string | null
  participants: string[]
  priority: EventPriority
  reminders: number[]
  recurrence: string | null
  status: EventStatus
  created_at: string
}

export interface EventFormValues {
  title: string
  description: string
  start_time: string
  end_time: string
  location: string
  priority: EventPriority
  repeat: RepeatOption
}

// Traduz a opção simples escolhida no formulário para a string de recorrência
// guardada no banco. O usuário nunca vê "FREQ=WEEKLY;INTERVAL=1".
const REPEAT_TO_RECURRENCE: Record<RepeatOption, string | null> = {
  none: null,
  daily: 'FREQ=DAILY;INTERVAL=1',
  weekly: 'FREQ=WEEKLY;INTERVAL=1',
  monthly: 'FREQ=MONTHLY;INTERVAL=1',
}

const RECURRENCE_LABELS: { match: (rule: string) => boolean; label: string }[] = [
  { match: (r) => r.includes('FREQ=DAILY'), label: 'Repete todo dia' },
  { match: (r) => r.includes('FREQ=WEEKLY'), label: 'Repete toda semana' },
  { match: (r) => r.includes('FREQ=MONTHLY'), label: 'Repete todo mês' },
]

export function repeatOptionToRecurrence(repeat: RepeatOption): string | null {
  return REPEAT_TO_RECURRENCE[repeat]
}

export function recurrenceToRepeatOption(recurrence: string | null): RepeatOption {
  if (!recurrence) return 'none'
  if (recurrence.includes('FREQ=DAILY')) return 'daily'
  if (recurrence.includes('FREQ=WEEKLY')) return 'weekly'
  if (recurrence.includes('FREQ=MONTHLY')) return 'monthly'
  return 'none'
}

export function describeRecurrence(recurrence: string | null): string | null {
  if (!recurrence) return null
  const match = RECURRENCE_LABELS.find((entry) => entry.match(recurrence))
  return match?.label ?? 'Repete periodicamente'
}

export async function fetchEvents(externalId: string): Promise<CalendarEvent[]> {
  const { data } = await api.get<CalendarEvent[]>('/calendar/events', {
    params: { external_id: externalId },
  })
  return data
}

export async function createEvent(externalId: string, values: EventFormValues): Promise<CalendarEvent> {
  const { data } = await api.post<CalendarEvent>('/calendar/events', {
    external_id: externalId,
    title: values.title,
    description: values.description || null,
    start_time: values.start_time,
    end_time: values.end_time,
    location: values.location || null,
    priority: values.priority,
    recurrence: repeatOptionToRecurrence(values.repeat),
  })
  return data
}

export async function updateEvent(
  eventId: number,
  values: EventFormValues
): Promise<CalendarEvent> {
  const { data } = await api.put<CalendarEvent>(`/calendar/events/${eventId}`, {
    title: values.title,
    description: values.description || null,
    start_time: values.start_time,
    end_time: values.end_time,
    location: values.location || null,
    priority: values.priority,
    recurrence: repeatOptionToRecurrence(values.repeat),
  })
  return data
}

export async function cancelEvent(eventId: number): Promise<void> {
  await api.delete(`/calendar/events/${eventId}`)
}

import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format, isToday, isTomorrow, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { CalendarPlus, Loader2, MapPin, Pencil, Repeat, Search, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { useExternalId } from '@/hooks/useExternalId'
import {
  cancelEvent,
  createEvent,
  describeRecurrence,
  fetchEvents,
  recurrenceToRepeatOption,
  updateEvent,
  type CalendarEvent,
  type EventFormValues,
  type EventPriority,
  type RepeatOption,
} from '@/api/calendar'

const PRIORITY_LABELS: Record<EventPriority, string> = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
}

const PRIORITY_COLORS: Record<EventPriority, string> = {
  low: 'bg-muted text-muted-foreground',
  medium: 'bg-primary/10 text-primary',
  high: 'bg-destructive/10 text-destructive',
}

const REPEAT_LABELS: Record<RepeatOption, string> = {
  none: 'Não repetir',
  daily: 'Todo dia',
  weekly: 'Toda semana',
  monthly: 'Todo mês',
}

const EMPTY_FORM: EventFormValues = {
  title: '',
  description: '',
  start_time: '',
  end_time: '',
  location: '',
  priority: 'medium',
  repeat: 'none',
}

export default function Agenda() {
  const { externalId, searchInput, setSearchInput, handleSearch } = useExternalId()
  const [modalOpen, setModalOpen] = useState(false)
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null)
  const [form, setForm] = useState<EventFormValues>(EMPTY_FORM)
  const queryClient = useQueryClient()

  const eventsQuery = useQuery({
    queryKey: ['calendar-events', externalId],
    queryFn: () => fetchEvents(externalId),
    enabled: !!externalId,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['calendar-events', externalId] })

  const createMutation = useMutation({
    mutationFn: (values: EventFormValues) => createEvent(externalId, values),
    onSuccess: () => {
      toast.success('Evento criado!')
      invalidate()
      setModalOpen(false)
    },
    onError: () => toast.error('Não foi possível criar o evento.'),
  })

  const updateMutation = useMutation({
    mutationFn: (values: EventFormValues) => updateEvent(editingEvent!.id, values),
    onSuccess: () => {
      toast.success('Evento atualizado!')
      invalidate()
      setModalOpen(false)
    },
    onError: () => toast.error('Não foi possível atualizar o evento.'),
  })

  const cancelMutation = useMutation({
    mutationFn: (eventId: number) => cancelEvent(eventId),
    onSuccess: () => {
      toast.success('Evento cancelado.')
      invalidate()
    },
    onError: () => toast.error('Não foi possível cancelar o evento.'),
  })

  const openCreateModal = () => {
    setEditingEvent(null)
    setForm(EMPTY_FORM)
    setModalOpen(true)
  }

  const openEditModal = (event: CalendarEvent) => {
    setEditingEvent(event)
    setForm({
      title: event.title,
      description: event.description || '',
      start_time: toLocalInputValue(event.start_time),
      end_time: toLocalInputValue(event.end_time),
      location: event.location || '',
      priority: event.priority,
      repeat: recurrenceToRepeatOption(event.recurrence),
    })
    setModalOpen(true)
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!form.title.trim() || !form.start_time || !form.end_time) {
      toast.error('Preencha título, início e fim do evento.')
      return
    }
    if (editingEvent) {
      updateMutation.mutate(form)
    } else {
      createMutation.mutate(form)
    }
  }

  const groupedEvents = useMemo(() => groupEventsByDay(eventsQuery.data ?? []), [eventsQuery.data])
  const isSaving = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Agenda</h2>
        {externalId && (
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <CalendarPlus className="h-4 w-4" />
            Novo evento
          </button>
        )}
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
          Informe o ID do usuário acima para ver a agenda.
        </div>
      )}

      {externalId && eventsQuery.isLoading && (
        <div className="p-10 flex justify-center text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      )}

      {externalId && eventsQuery.isError && (
        <div className="p-10 text-center text-sm text-destructive bg-card border border-border rounded-xl">
          Não foi possível carregar a agenda.
        </div>
      )}

      {externalId && eventsQuery.data?.length === 0 && (
        <div className="p-10 text-center text-muted-foreground bg-card border border-border rounded-xl">
          Nenhum evento agendado. Clique em "Novo evento" para começar.
        </div>
      )}

      {externalId && groupedEvents.length > 0 && (
        <div className="space-y-6">
          {groupedEvents.map((group) => (
            <div key={group.key}>
              <h3 className="text-sm font-semibold text-muted-foreground mb-2 capitalize">{group.label}</h3>
              <div className="space-y-2">
                {group.events.map((event) => (
                  <EventCard
                    key={event.id}
                    event={event}
                    onEdit={() => openEditModal(event)}
                    onCancel={() => cancelMutation.mutate(event.id)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingEvent ? 'Editar evento' : 'Novo evento'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-foreground">Título</label>
            <Input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Ex: Reunião com o time"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Início</label>
              <Input
                type="datetime-local"
                value={form.start_time}
                onChange={(e) => setForm({ ...form, start_time: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Fim</label>
              <Input
                type="datetime-local"
                value={form.end_time}
                onChange={(e) => setForm({ ...form, end_time: e.target.value })}
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-foreground">Local (opcional)</label>
            <Input
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              placeholder="Ex: Escritório, link da chamada..."
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-foreground">Descrição (opcional)</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Prioridade</label>
              <select
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value as EventPriority })}
                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {(Object.entries(PRIORITY_LABELS) as [EventPriority, string][]).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Repetir</label>
              <select
                value={form.repeat}
                onChange={(e) => setForm({ ...form, repeat: e.target.value as RepeatOption })}
                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {(Object.entries(REPEAT_LABELS) as [RepeatOption, string][]).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 rounded-md text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {isSaving ? 'Salvando...' : editingEvent ? 'Salvar alterações' : 'Criar evento'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

function EventCard({
  event,
  onEdit,
  onCancel,
}: {
  event: CalendarEvent
  onEdit: () => void
  onCancel: () => void
}) {
  const recurrenceLabel = describeRecurrence(event.recurrence)
  const isCancelled = event.status === 'cancelled'

  return (
    <div
      className={`p-4 bg-card border border-border rounded-xl flex items-start justify-between gap-4 ${
        isCancelled ? 'opacity-60' : ''
      }`}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-foreground">
            {format(parseISO(event.start_time), 'HH:mm')} – {format(parseISO(event.end_time), 'HH:mm')}
          </span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${PRIORITY_COLORS[event.priority]}`}>
            {PRIORITY_LABELS[event.priority]}
          </span>
          {isCancelled && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-destructive/10 text-destructive">
              Cancelado
            </span>
          )}
        </div>
        <p className="font-semibold text-foreground mt-1 truncate">{event.title}</p>
        {event.location && (
          <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            {event.location}
          </p>
        )}
        {recurrenceLabel && (
          <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
            <Repeat className="h-3 w-3" />
            {recurrenceLabel}
          </p>
        )}
      </div>

      {!isCancelled && (
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={onEdit}
            className="p-2 rounded-md hover:bg-muted text-muted-foreground transition-colors"
            title="Editar"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            onClick={onCancel}
            className="p-2 rounded-md hover:bg-destructive/10 text-destructive transition-colors"
            title="Cancelar"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}

function toLocalInputValue(isoString: string): string {
  // datetime-local espera "YYYY-MM-DDTHH:mm" no horário local, sem timezone.
  const date = parseISO(isoString)
  const offset = date.getTimezoneOffset()
  const local = new Date(date.getTime() - offset * 60000)
  return local.toISOString().slice(0, 16)
}

function groupEventsByDay(
  events: CalendarEvent[]
): { key: string; label: string; events: CalendarEvent[] }[] {
  const groups = new Map<string, CalendarEvent[]>()

  for (const event of events) {
    const day = event.start_time.slice(0, 10)
    if (!groups.has(day)) groups.set(day, [])
    groups.get(day)!.push(event)
  }

  return Array.from(groups.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, dayEvents]) => ({
      key,
      label: describeDay(parseISO(key)),
      events: dayEvents,
    }))
}

function describeDay(date: Date): string {
  if (isToday(date)) return 'Hoje'
  if (isTomorrow(date)) return 'Amanhã'
  return format(date, "EEEE, d 'de' MMMM", { locale: ptBR })
}

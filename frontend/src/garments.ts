export type RackGroup = 'all' | 'hoodies' | 'tshirts' | 'crewnecks' | 'jackets' | 'more'

export const RACK_GROUPS: { id: RackGroup; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'hoodies', label: 'Hoodies' },
  { id: 'tshirts', label: 'T-shirts' },
  { id: 'crewnecks', label: 'Crewnecks' },
  { id: 'jackets', label: 'Jackets' },
  { id: 'more', label: 'More' },
]

export function garmentGroup(garmentType: string | undefined): Exclude<RackGroup, 'all'> {
  const label = (garmentType || '').toLowerCase()
  if (label.includes('t-shirt')) return 'tshirts'
  if (label.includes('hoodie') || label.includes('hooded')) return 'hoodies'
  if (label.includes('crewneck')) return 'crewnecks'
  if (label.includes('jacket') || label.includes('fleece')) return 'jackets'
  return 'more'
}

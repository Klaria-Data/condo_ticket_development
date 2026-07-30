export function getInitials(name: string): string {
  // split(/\s+/) evita que espaços repetidos virem uma parte vazia e gerem "JUNDEFINED".
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();

  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}
export default function KGMetadata({
  model,
  backend,
  timestamp,
  confidence,
}: {
  model: string
  backend: string
  timestamp: string
  confidence: string
}) {
  return (
    <footer className="border-t border-stone-200 pt-4 text-xs text-stone-500 font-mono flex flex-wrap gap-x-6 gap-y-1">
      <span>model: {model}</span>
      <span>backend: {backend}</span>
      <span>confidence: {confidence}</span>
      <span>generated: {new Date(timestamp).toLocaleString()}</span>
      <span>ontology: w3id.org/aief</span>
    </footer>
  )
}

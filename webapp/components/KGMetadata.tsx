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
    <footer className="flex shrink-0 flex-wrap gap-x-4 gap-y-0.5 font-mono text-[10px] text-stone-500">
      <span>model: {model}</span>
      <span>backend: {backend}</span>
      <span>confidence: {confidence}</span>
      <span>generated: {new Date(timestamp).toLocaleString()}</span>
      <span>ontology: w3id.org/aief</span>
    </footer>
  )
}

import { useStore } from '../store/StoreContext'

export default function Toast() {
  const { toastText } = useStore()
  return <div className="toast" role="status" hidden={!toastText}>{toastText}</div>
}

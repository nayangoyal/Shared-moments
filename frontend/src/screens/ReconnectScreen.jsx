import { EMPTY_FORM, EXAMPLE_FORM, HOW } from '../data/data'
import { go } from '../hooks/useHashRoute'
import { reconnectScore } from '../lib/utils'
import { useStore } from '../store/StoreContext'
import { Chips, Intro, Meter, TopBar } from '../components/ui'

const FIELDS = [
  { k: 'name', label: 'Their name', ph: 'e.g. Aarav Mehta' },
  { k: 'nick', label: 'Nickname you called them', hint: '(if any)', ph: 'e.g. Chintu' },
]
const FIELDS2 = [
  { k: 'school', label: 'School or college', ph: 'e.g. St. Stanislaus' },
  { k: 'year', label: 'Year', ph: 'e.g. 2014', mode: 'numeric' },
  { k: 'area', label: 'Old area or city', ph: 'e.g. Pali Hill, Bandra' },
  { k: 'phone', label: 'Old phone number', hint: '(if you still have it)', ph: 'e.g. 98201 44120', mode: 'tel' },
]

function Field({ f, value, onChange }) {
  const id = 'f-' + f.k
  return (
    <div className="field">
      <label htmlFor={id}>{f.label} {f.hint && <span className="hint">{f.hint}</span>}</label>
      <input className="input" id={id} inputMode={f.mode} placeholder={f.ph} value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  )
}

// Reconnect: describe a lost friend. Submitting saves a private request; matches show up in Reunited.
export default function ReconnectScreen() {
  const { form: rf, setForm, submitRequest, setOpen, toast } = useStore()
  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }))

  const n = reconnectScore(rf)
  const level = n < 4 ? 'low' : n < 7 ? 'mid' : 'high'
  const text = n < 4 ? 'Your chances: low. Add a few more details.' : n < 7 ? 'Your chances: good. A little more helps.' : 'Your chances: great. Lots of detail to go on.'

  const start = () => {
    if (!Object.values(rf).some((v) => v.trim())) { toast('Fill in at least one thing you remember'); return }
    submitRequest('re', { ...rf })
    setForm(EMPTY_FORM)
    setOpen('re', null)
    go('reunited')
    toast("Request saved. We'll look out for them.")
  }

  return (
    <>
      <TopBar title="Reconnect" />
      <div className="screen">
        <Intro title="Who are you looking for?">
          A school friend, an old neighbour, a first-job buddy. Describe them and we'll look out for them. Only you can see this.
        </Intro>
        <div className="mainbox formgrid">
          <div className="tip span"><b>Nothing here is required, but the more you fill in, the better your chances of finding them.</b></div>
          {FIELDS.map((f) => <Field key={f.k} f={f} value={rf[f.k]} onChange={set(f.k)} />)}
          <div className="field span">
            <span className="lab">How did you know them?</span>
            <Chips options={HOW} selected={(h) => rf.how === h} onToggle={(h) => set('how')(rf.how === h ? '' : h)} />
          </div>
          {FIELDS2.map((f) => <Field key={f.k} f={f} value={rf[f.k]} onChange={set(f.k)} />)}
          <div className="field span">
            <label htmlFor="f-memory">A memory you share</label>
            <span className="hint">Where you met, what you did together, when you lost touch.</span>
            <textarea className="input" id="f-memory" value={rf.memory} onChange={(e) => set('memory')(e.target.value)}
              placeholder="e.g. We sat on the last bench in 7th standard and played cricket every recess…" />
            <Meter pct={Math.round((n / 10) * 100)} level={level} text={text} />
          </div>
          <div className="sticky-go span">
            <button className="btn main full" type="button" onClick={start}>Start looking</button>
            <button className="link center" type="button" onClick={() => setForm({ ...EXAMPLE_FORM })}>Fill an example</button>
          </div>
        </div>
      </div>
    </>
  )
}

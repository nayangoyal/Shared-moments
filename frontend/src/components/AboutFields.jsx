// The "About you" fields, shared by the first-time screen and the Profile page.
export const EMPTY_ABOUT = { name: '', age: '', place: '', nick: '', school: '', year: '', area: '' }

const YOU = [
  { k: 'name', label: 'Your name', ph: 'e.g. Nayan Goyal', span: true },
  { k: 'age', label: 'Age', ph: 'e.g. 24', mode: 'numeric' },
  { k: 'place', label: 'Where you live now', ph: 'e.g. Jaipur' },
]
const THEN = [
  { k: 'nick', label: 'What friends called you', hint: '(nicknames)', ph: 'e.g. Golu' },
  { k: 'school', label: 'School or college', hint: '(add more with commas)', ph: 'e.g. Army Public School' },
  { k: 'year', label: 'Year', ph: 'e.g. 2012', mode: 'numeric' },
  { k: 'area', label: 'Areas you grew up in', ph: 'e.g. Nasirabad; Pali Hill, Bandra' },
]

export default function AboutFields({ value, onChange }) {
  const field = (f) => (
    <div className={'field' + (f.span ? ' span' : '')} key={f.k}>
      <label htmlFor={'a-' + f.k}>{f.label} {f.hint && <span className="hint">{f.hint}</span>}</label>
      <input className="input" id={'a-' + f.k} inputMode={f.mode} placeholder={f.ph} value={value[f.k] || ''}
        onChange={(e) => onChange({ ...value, [f.k]: e.target.value })} />
    </div>
  )
  return (
    <>
      {YOU.map(field)}
      <div className="span sub-head">How old friends would remember you</div>
      {THEN.map(field)}
    </>
  )
}

// Help cards shown beside each tab (below it on small screens)
const Card = ({ title, children }) => <div className="card"><h3>{title}</h3>{children}</div>

const SIDE = {
  reconnect: (
    <>
      <Card title="How Reconnect works">
        <ol>
          <li>Describe the friend you lost.</li>
          <li>We keep it as your private request.</li>
          <li>When someone on the site matches it, you'll see "This might be your moment".</li>
          <li>Say hi and chat.</li>
        </ol>
      </Card>
      <Card title="Only you see this"><p>Nobody can read your request. If you match, they only see your message.</p></Card>
    </>
  ),
  reunited: (
    <>
      <Card title="About Reunited"><p>Your requests wait here until someone matches. A match is only a maybe: say hi if it looks right, or tap "Not them".</p></Card>
      <Card title="Still waiting?">
        <p>Your friend may not have joined yet. Your request stays active and matches when they do. Meanwhile, meet new people.</p>
        <a className="btn small main" href="#meet">Meet new people</a>
      </Card>
    </>
  ),
  meet: (
    <>
      <Card title="How Meet New works">
        <ol>
          <li>Pick what you'd like to do.</li>
          <li>Describe the moment in detail.</li>
          <li>We match you with people who want the same.</li>
          <li>Matches show up in New Friends.</li>
        </ol>
      </Card>
      <Card title="Stay safe"><p>Everyone with a blue ✓ is verified. Meet first in a public place.</p></Card>
    </>
  ),
  newfriends: (
    <>
      <Card title="About New Friends"><p>Your requests, the people who match them, and the friends you're chatting with.</p></Card>
      <Card title="Stay safe"><p>Meet first in a public place and tell someone at home where you're going.</p></Card>
    </>
  ),
}

export default function SidePanel({ route }) {
  return <aside className="side" aria-label="Help">{SIDE[route]}</aside>
}

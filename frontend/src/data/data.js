// Sample data for the demo. Everything runs in the browser; nothing is sent to a server.
// People's own requests are private and never shown: you only see a name and what matched.

export const C = ['#c2552d', '#3d6fb6', '#2f7a4f', '#8a5a9e', '#b5832a', '#4f7f86']

// Old friends on the site (matched by Reconnect requests)
export const OLD = [
  { id: 'aarav', n: 'Aarav Mehta', nick: 'Chintu', a: 24, school: 'St. Stanislaus School', year: '2014', area: 'Pali Hill, Bandra', how: 'Classmate', place: 'Mumbai', c: C[1] },
  { id: 'farah', n: 'Farah Sheikh', nick: 'Fizz', a: 24, school: 'St. Stanislaus School', year: '2014', area: 'Bandra West', how: 'Classmate', place: 'Thane', c: C[4] },
  { id: 'zoya', n: 'Zoya Khan', nick: '', a: 23, school: 'Holy Cross School', year: '2015', area: 'Kurla West', how: 'Neighbour', place: 'Mumbai', c: C[3] },
  { id: 'meena', n: 'Meena Iyer', nick: 'Meenu', a: 58, school: 'SIES College', year: '1987', area: 'Matunga', how: 'Neighbour', place: 'Chembur', c: C[5] },
]

// New people nearby (matched by Meet New requests)
export const PEOPLE = [
  { id: 'ishaan', n: 'Ishaan', a: 23, place: 'Bandra · 1 km', acts: ['Walks', 'Chai or coffee', 'Sunsets'], c: C[0] },
  { id: 'sunita', n: 'Sunita', a: 52, place: 'Santacruz · 3 km', acts: ['Walks', 'Cooking', 'Music'], c: C[4] },
  { id: 'meher', n: 'Meher', a: 22, place: 'Khar · 2 km', acts: ['Board games', 'Chai or coffee', 'Movies'], c: C[3] },
  { id: 'desai', n: 'Mr. Desai', a: 67, place: 'Bandra · 1 km', acts: ['Walks', 'Photography', 'Chai or coffee'], c: C[5] },
  { id: 'rohan', n: 'Rohan', a: 24, place: 'Juhu · 4 km', acts: ['Cricket', 'Treks', 'Sunsets'], c: C[2] },
  { id: 'dev', n: 'Dev', a: 26, place: 'Mahim · 3 km', acts: ['Music', 'Sunsets', 'Movies'], c: C[1] },
]

// Demo: the first reply each person sends after you say hi
export const REPLY = {
  aarav: "Chintu here! I can't believe it. How have you been all these years?",
  farah: "Oh my god, hi!! It's been more than 10 years!",
  zoya: "Yes it's me! Building 4!",
  meena: 'What a lovely surprise! Come over for filter coffee, like old times.',
  ishaan: 'Hey! Yes, let\'s do it. Carter Road at 7?',
  sunita: "Hello! I'd love a walking buddy. Mornings suit me best.",
  meher: 'Hi! Carrom this weekend?',
  desai: 'Hello young friend! Join me for the Sunday morning walk.',
  rohan: 'Hey! Sunday match at Juhu?',
  dev: "Hi! There's an open mic on Friday, come along.",
}

export const byId = (id) => [...OLD, ...PEOPLE].find((p) => p.id === id)

export const HOW = ['Classmate', 'Neighbour', 'Colleague', 'Family friend', 'Other']
export const ACTS = ['Walks', 'Chai or coffee', 'Sunsets', 'Board games', 'Music', 'Cooking', 'Cricket', 'Photography', 'Treks', 'Movies']
export const WHEN = ['This weekend', 'Weekday evenings', 'Mornings', 'Any time']
export const MIN_WORDS = 20

// "If your friend isn't on the site" notes for the judges. live = working in this demo
export const SOLS = [
  { t: 'Your request waits for them', d: "If your friend isn't on the site yet, your request stays active. When they join and describe you, we match you both.", live: true },
  { t: 'Kind words, no dead end', d: '"No match yet", never "user not found". And a button to meet new people meanwhile.', live: true },
  { t: 'Private by design', d: "Nobody can see your request, and you can't see theirs. When you match, you only see a name and what matched from your own words.", live: true },
  { t: 'You choose to say hi', d: 'A match is only a "maybe". You decide whether to text them, or tap "Not them".', live: true },
  { t: 'Smarter matching', d: 'Read the whole description (memories, places, nicknames), not just the fields.', live: false },
  { t: 'Tell me by SMS or email', d: 'A message when a match appears, so you don\'t have to keep checking.', live: false },
]

// Labels for showing a saved request
export const LABELS = {
  name: 'Name', nick: 'Nickname', how: 'How you knew them', school: 'School or college', year: 'Year', area: 'Old area',
  phone: 'Old phone', memory: 'Shared memory', acts: 'Wants to do', when: 'When', where: 'Where', desc: 'Description',
}

export const EMPTY_FORM = { name: '', nick: '', how: '', school: '', year: '', area: '', phone: '', memory: '' }

export const EXAMPLE_FORM = {
  name: 'Aarav', nick: 'Chintu', how: 'Classmate', school: 'St. Stanislaus', year: '2014', area: 'Pali Hill', phone: '',
  memory: "We sat on the last bench in 7th standard and played gully cricket behind the chapel every recess. He moved to Andheri after 10th and we lost touch. I'd love to grab a chai and talk about the old days.",
}

export const EMPTY_MEET = { picked: [], when: '', text: '', area: 'Bandra, Mumbai' }

export const EXAMPLE_MEET = {
  acts: ['Music', 'Sunsets'],
  when: 'This weekend',
  text: "I play the guitar a little and miss jamming with friends. I'd love to find a few people who enjoy music and sunsets, to sit by the sea on a weekend evening and play some old songs together.",
}

// Saved state. re = Reconnect/Reunited, nw = Meet New/New Friends.
// reqs: your private requests · moments: possible matches (not yet contacted) · chats: people you're talking to
export const seedOld = () => ({
  re: {
    reqs: [
      { id: 'r1', data: { name: 'Sonu', how: 'Classmate', school: 'Fergusson College', year: '2017', area: 'Kothrud, Pune', memory: 'We cycled to Sinhagad every Sunday at 5 am in second year and shared vada pav at the top. He moved to Bangalore after college and we lost touch.' } },
      { id: 'r2', data: { name: 'Aarav', nick: 'Chintu', how: 'Classmate', school: 'St. Stanislaus', year: '2014', area: 'Pali Hill', memory: 'We sat on the last bench in 7th standard and played gully cricket behind the chapel every recess.' } },
    ],
    moments: [{ pid: 'aarav', req: 'r2', why: ['name', 'nickname', 'school', 'year'] }],
    chats: ['zoya'],
  },
  nw: {
    reqs: [{ id: 'n1', data: { acts: 'Walks, Chai or coffee', when: 'Weekday evenings', where: 'Bandra, Mumbai', desc: "I've just moved to Bandra and walk at Carter Road most evenings around 7. Looking for a calm walking buddy, any age, who enjoys a cutting chai after." } }],
    moments: [{ pid: 'sunita', req: 'n1', why: ['Walks'] }],
    chats: ['ishaan'],
  },
  msgs: {
    zoya: [
      { me: true, t: 'Zoya! Is this you from Kurla West? We were neighbours in Building 4!' },
      { me: false, t: "Yes it's me! Building 4!" },
      { me: false, t: 'Do you still listen to those old songs?' },
    ],
    ishaan: [
      { me: true, t: 'Hi Ishaan! I walk at the sea face most evenings too. Chai sometime?' },
      { me: false, t: 'Yes! Thursday 7 pm at Carter Road?' },
    ],
  },
})

export const seedNew = () => ({ re: { reqs: [], moments: [], chats: [] }, nw: { reqs: [], moments: [], chats: [] }, msgs: {} })

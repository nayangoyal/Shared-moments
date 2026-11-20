// Form options and example text. People, requests, matches and chats come from the API.

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
  { t: 'Smarter matching with Gemini', d: 'Gemini reads the whole description (memories, places, nicknames in any spelling), checks both people describe each other, and a judge model confirms the match.', live: true },
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

// "Fill an example" on About me: the person Aarav (a demo user) is looking for
export const EXAMPLE_ABOUT = {
  name: 'Rahul Sharma', age: '24', place: 'Bandra, Mumbai', nick: 'Golu',
  school: 'St. Stanislaus School', year: '2014', area: 'Pali Hill, Bandra; Kurla West',
}

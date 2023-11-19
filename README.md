### known bugs:
- In a cluster with subject `A` and leader `B`, we can send messages to `A`. Then `A.get_messages` and `B.get_messages`
  return different things. Problem is that there is no distinction between the interface used by clients and the interface
  used by the nodes among themselves.
- In a cluster with leader `A` and subject `B` and two other subjects, if we send a message while the other two subjects
  are down, and then get into a state where `B` becomes leader, then `B.get_messages` will return the message even though
  no consensus was reached on the message. Core of the problem is that subjects and candidates make no distinction between
  committed and non-committed messages
- Suppose in a cluster with four nodes `A` through `D`, that `A` and `B` become candidates at the same time, and request votes
  from `C` and `D`, respectively. Then the election fails and `A` and `B` become subjects again. If this then repeats,
  `C` and `D` are again unable to vote, and the next election fails too. This bug is hard to detect, because at some point
  `C` or `D` will become a candidate, and the election will succeed. And moreover it depends on two nodes becoming candidates
  at exactly the same time, so it's rare to begin with.
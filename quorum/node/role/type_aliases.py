from quorum.node.role.subject import Subject
from quorum.node.role.candidate import Candidate
from quorum.node.role.leader import Leader

UpRole = Leader | Subject | Candidate

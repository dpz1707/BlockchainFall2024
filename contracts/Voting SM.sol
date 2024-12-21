// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";

contract SecureVoting is Ownable {
    struct Candidate {
        string name;
        uint256 voteCount;
    }

    struct Voter {
        bool hasVoted;
        uint256 votedCandidateId;
    }

    mapping(address => Voter) public voters;
    Candidate[] public candidates;
    bool public votingOpen;

    event VoteCast(address indexed voter, uint256 candidateId);
    event VotingStarted();
    event VotingEnded();

    // Pass msg.sender to Ownable constructor
    constructor(string[] memory candidateNames) Ownable(msg.sender) {
        for (uint256 i = 0; i < candidateNames.length; i++) {
            candidates.push(
                Candidate({
                    name: candidateNames[i],
                    voteCount: 0
                })
            );
        }
        votingOpen = false;
    }

    modifier onlyWhileOpen() {
        require(votingOpen, "Voting is not open");
        _;
    }

    function startVoting() public onlyOwner {
        votingOpen = true;
        emit VotingStarted();
    }

    function endVoting() public onlyOwner {
        votingOpen = false;
        emit VotingEnded();
    }

    function vote(uint256 candidateId) public onlyWhileOpen {
        require(!voters[msg.sender].hasVoted, "You have already voted");
        require(candidateId < candidates.length, "Invalid candidate ID");

        voters[msg.sender].hasVoted = true;
        voters[msg.sender].votedCandidateId = candidateId;
        candidates[candidateId].voteCount++;

        emit VoteCast(msg.sender, candidateId);
    }

    function getCandidates() public view returns (Candidate[] memory) {
        return candidates;
    }

    function getVoteCount(uint256 candidateId) public view returns (uint256) {
        require(candidateId < candidates.length, "Invalid candidate ID");
        return candidates[candidateId].voteCount;
    }
}

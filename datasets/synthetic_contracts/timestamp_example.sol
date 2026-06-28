// SPDX-License-Identifier: MIT
// SYNTHETIC ILLUSTRATIVE EXAMPLE — authored for this artifact's offline demo.
// This is NOT from the ESC/VSC dataset. It shows timestamp-dependence: contract
// logic and fund release gated on block.timestamp, which a miner can nudge.
pragma solidity ^0.8.0;

contract TimedLottery {
    address public winner;
    uint256 public deadline;

    constructor() { deadline = block.timestamp + 1 days; }

    // VULNERABLE: uses block.timestamp both as a branch condition and as a
    // pseudo-random source to pick the winner.
    function draw() external {
        require(block.timestamp >= deadline, "too early");
        if (block.timestamp % 2 == 0) {
            winner = msg.sender;
            payable(msg.sender).transfer(address(this).balance);
        }
    }
}

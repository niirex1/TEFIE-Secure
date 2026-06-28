// SPDX-License-Identifier: MIT
// SYNTHETIC ILLUSTRATIVE EXAMPLE — authored for this artifact's offline demo.
// This is NOT from the ESC/VSC dataset. It shows an unbounded loop over an
// attacker-growable array, which can exceed the block gas limit (DoS).
pragma solidity ^0.8.0;

contract Airdrop {
    address[] public recipients;

    function join() external { recipients.push(msg.sender); }

    // VULNERABLE: iterates the whole recipients array with no bound; once the
    // array is large enough the loop runs out of gas and the function bricks.
    function payout(uint256 amount) external {
        for (uint256 i = 0; i < recipients.length; i++) {
            payable(recipients[i]).transfer(amount);
        }
    }
}

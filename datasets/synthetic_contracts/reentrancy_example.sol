// SPDX-License-Identifier: MIT
// SYNTHETIC ILLUSTRATIVE EXAMPLE — authored for this artifact's offline demo.
// This is NOT from the ESC/VSC dataset. It shows the classic reentrancy pattern
// (external call before state update) so the demo has a positive reentrancy case.
pragma solidity ^0.8.0;

contract VulnerableVault {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // VULNERABLE: sends funds before zeroing the balance, allowing the callee
    // to re-enter withdraw() and drain the contract.
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "no balance");
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");
        balances[msg.sender] = 0; // state update AFTER the external call
    }
}

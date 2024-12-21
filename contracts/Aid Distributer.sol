// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CharityDistributor {
    address public owner;


    struct Recipient {
        address wallet;
        uint256 share; // ratio of funds given
    }

    Recipient[] public recipients;
    uint256 public totalShares; // Sum of all shares

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
    }


    receive() external payable {}
    fallback() external payable {}


    function addRecipient(address _wallet, uint256 _share) external onlyOwner {
        require(_wallet != address(0), "Invalid address");
        require(_share > 0, "Share must be greater than 0");

        recipients.push(Recipient(_wallet, _share));
        totalShares += _share;
    }


    function updateRecipientShare(uint256 index, uint256 newShare) external onlyOwner {
        require(index < recipients.length, "Invalid index");
        require(newShare > 0, "Share must be greater than 0");

        totalShares = totalShares - recipients[index].share + newShare;
        recipients[index].share = newShare;
    }

    function removeRecipient(uint256 index) external onlyOwner {
        require(index < recipients.length, "Invalid index");

        totalShares -= recipients[index].share;

        recipients[index] = recipients[recipients.length - 1];
        recipients.pop();
    }

    function distributeFunds() external onlyOwner {
        require(recipients.length > 0, "No recipients to distribute to");
        require(totalShares > 0, "Total shares must be greater than zero");

        uint256 contractBalance = address(this).balance;
        require(contractBalance > 0, "No funds to distribute");

        for (uint256 i = 0; i < recipients.length; i++) {
            uint256 payment = (contractBalance * recipients[i].share) / totalShares;
            (bool sent, ) = recipients[i].wallet.call{value: payment}("");
            require(sent, "Failed to send Ether");
        }
    }

    function getRecipientsCount() external view returns (uint256) {
        return recipients.length;
    }

    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}

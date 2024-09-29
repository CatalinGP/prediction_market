// SPDX-License-Identifier: MIT
pragma solidity ^0.8.27;

// solhint-disable-next-line error-reason
contract PredictionMarket {
    event PoolCreated(uint256 poolId, address creator, uint256 targetPrice, uint256 stopLoss, uint256 endTime);
    event PoolFinalized(uint256 poolId, uint256 finalPrice, string outcome);

    struct Pool {
        address creator;
        uint256 targetPrice;
        uint256 stopLoss;
        uint256 endTime;
        bool isFinalized;
        uint256 finalPrice;
        string outcome;
    }

    mapping(uint256 => Pool) public pools;
    uint256 public poolCounter;

    uint256[] public activePools;

    // solhint-disable-next-line gas-custom-errors
    modifier poolExists(uint256 poolId) {
        require(poolId < poolCounter, "Pool does not exist");
        _;
    }

    function createPool(uint256 targetPrice, uint256 stopLoss, uint256 duration) external {
        uint256 endTime = block.timestamp + duration;

        pools[poolCounter] = Pool({
            creator: msg.sender,
            targetPrice: targetPrice,
            stopLoss: stopLoss,
            endTime: endTime,
            isFinalized: false,
            finalPrice: 0,
            outcome: ""
        });

        activePools.push(poolCounter);
        emit PoolCreated(poolCounter, msg.sender, targetPrice, stopLoss, endTime);
        poolCounter++;
    }

    // solhint-disable-next-line gas-custom-errors
    function resolvePool(uint256 poolId, uint256 currentPrice) external poolExists(poolId) {
        Pool storage pool = pools[poolId];
        require(!pool.isFinalized, "Pool already finalized");

        // solhint-disable-next-line gas-custom-errors
        // slither-disable-next-line timestamp
        require(
            block.timestamp >= pool.endTime || currentPrice >= pool.targetPrice || currentPrice <= pool.stopLoss,
            "Conditions not met for finalization"
        );

        if (currentPrice >= pool.targetPrice) {
            pool.outcome = "Target price reached";
        } else if (currentPrice <= pool.stopLoss) {
            pool.outcome = "Stop loss hit";
        } else {
            pool.outcome = "End time reached";
        }

        pool.finalPrice = currentPrice;
        pool.isFinalized = true;

        emit PoolFinalized(poolId, currentPrice, pool.outcome);
        _removeFromActivePools(poolId);
    }

    function getActivePools() external view returns (uint256[] memory) {
        return activePools;
    }

    function _removeFromActivePools(uint256 poolId) internal {
        for (uint256 i = 0; i < activePools.length; i++) {
            if (activePools[i] == poolId) {
                activePools[i] = activePools[activePools.length - 1];
                activePools.pop();
                break;
            }
        }
    }
}

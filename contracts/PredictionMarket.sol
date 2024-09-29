// SPDX-License-Identifier: MIT
pragma solidity >=0.7.3 <0.9.0;

contract PredictionMarket {
    event PoolCreated(uint256 poolId, address creator, uint256 targetPrice, uint256 stopLoss, uint256 endTime);
    event PoolFinalized(uint256 poolId, uint256 finalPrice, string outcome);

    struct Pool {
        address creator;
        uint256 targetPrice; // Target price to hit for a win
        uint256 stopLoss;    // Stop loss price to close the pool
        uint256 endTime;     // Time at which the pool ends
        bool isFinalized;    // Indicates if the pool is finalized
        uint256 finalPrice;  // The final price when the pool is closed
        string outcome;      // Outcome message of the pool
    }

    mapping(uint256 => Pool) public pools;
    uint256 public poolCounter;

    uint256[] public activePools;

    modifier poolExists(uint256 poolId) {
        require(poolId < poolCounter, "Pool does not exist");
        _;
    }

    function createPool(uint256 _targetPrice, uint256 _stopLoss, uint256 _duration) external {
        uint256 endTime = block.timestamp + _duration;

        pools[poolCounter] = Pool({
            creator: msg.sender,
            targetPrice: _targetPrice,
            stopLoss: _stopLoss,
            endTime: endTime,
            isFinalized: false,
            finalPrice: 0,
            outcome: ""
        });

        activePools.push(poolCounter);
        emit PoolCreated(poolCounter, msg.sender, _targetPrice, _stopLoss, endTime);

        poolCounter++;
    }

    function resolvePool(uint256 poolId, uint256 currentPrice) external poolExists(poolId) {
        Pool storage pool = pools[poolId];
        require(!pool.isFinalized, "Pool already finalized");
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
                activePools.pop();  // Remove the last element
                break;
            }
        }
    }
}

import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

const config: HardhatUserConfig = {
  solidity: "0.8.27",
};

module.exports = {
  solidity: "0.8.27",
  networks: {
    hardhat: {
      chainId: 84532,
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 84532,
    },
  },
};

export default config;

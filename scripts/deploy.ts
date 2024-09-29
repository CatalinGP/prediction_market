import { ethers } from "hardhat";
import { runAudit } from "./audit";

async function main() {
  const PredictionMarket = await ethers.getContractFactory("PredictionMarket");
  const predictionMarket = await PredictionMarket.deploy();

  // await predictionMarket.deployed();
  console.log("PredictionMarket deployed to:", predictionMarket.target);

  console.log("Running post-deployment audit...");
  await runAudit();
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

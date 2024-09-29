import { exec } from "child_process";

function runSolhint(): Promise<void> {
  return new Promise((resolve, reject) => {
    exec("npx solhint 'contracts/**/*.sol'", (error, stdout, stderr) => {
      if (error) {
        console.error(`Solhint Error: ${error.message}`);
        reject(error);
      }
      if (stderr) {
        console.error(`Solhint Stderr: ${stderr}`);
      }
      console.log(`Solhint Output:\n${stdout}`);
      resolve();
    });
  });
}

function runSlither(): Promise<void> {
  return new Promise((resolve, reject) => {
    exec("slither ./contracts", (error, stdout, stderr) => {
      if (error) {
        console.error(`Slither Error: ${error.message}`);
        reject(error);
      }
      if (stderr) {
        console.error(`Slither Stderr: ${stderr}`);
      }
      console.log(`Slither Output:\n${stdout}`);
      resolve();
    });
  });
}

export async function runAudit() {
  try {
    console.log("Running Solhint...");
    await runSolhint();

    console.log("Running Slither...");
    await runSlither();

    console.log("Audit completed.");
  } catch (error) {
    console.error("Audit failed:", error);
  }
}

const { execSync } = require('child_process');

// Wrap the main logic in an async function
const main = async () => {
  try {
    // Start core services
    console.log('Starting core services...');
    execSync(
      'docker compose -f docker-compose.test.yaml up -d gateway on-fhir-db on-fhir on-bullmq-redis on-transfer-outbound on-transfer-inbound bc-fhir-db bc-fhir bc-bullmq-redis bc-transfer-outbound bc-transfer-inbound',
      { stdio: 'inherit' },
    );

    // Wait for FHIR servers
    console.log('Waiting for FHIR servers...');
    execSync(
      'node ./node-dev-docker-env/wait_for_service.cjs http://localhost:8080/on/fhir/metadata',
      {
        stdio: 'inherit',
      },
    );
    execSync(
      'node ./node-dev-docker-env/wait_for_service.cjs http://localhost:8080/bc/fhir/metadata',
      {
        stdio: 'inherit',
      },
    );

    // Start synthesizer services after FHIR servers are up
    console.log('Starting synthesizer services...');
    execSync(
      'docker compose -f docker-compose.test.yaml up on-synthesizer bc-synthesizer',
      { stdio: 'inherit' },
    );

    // Run the test after synthesizers are started
    console.log('Starting test container...');
    execSync('docker compose -f docker-compose.test.yaml up uj1-pt-pt', {
      stdio: 'inherit',
    });
  } catch (error) {
    console.error('Test setup failed:', error.message);
    process.exit(1);
  }
};

main();

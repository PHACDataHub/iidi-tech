const { execSync } = require('child_process');
const { join } = require('path');

// Path to your wait script (adjust as needed)
const waitScript = join(
  __dirname,
  '../node-dev-docker-env/wait_for_service.cjs',
);

// Docker services to start (customize list as needed)
const coreServices = [
  'gateway',
  'on-fhir-db',
  'on-fhir',
  'on-bullmq-redis',
  'on-transfer-outbound',
  'bc-fhir-db',
  'bc-fhir',
  'bc-bullmq-redis',
  'bc-transfer-outbound',
];

try {
  // Start core services
  console.log('Starting core services...');
  execSync(
    `docker compose -f docker-compose.test.yaml up -d ${coreServices.join(' ')}`,
    { stdio: 'inherit' }, // Show Docker output
  );

  // Wait for FHIR servers
  console.log('Waiting for FHIR servers...');
  execSync(`node ${waitScript} http://localhost:8080/on/fhir/metadata`, {
    stdio: 'inherit',
  });
  execSync(`node ${waitScript} http://localhost:8080/bc/fhir/metadata`, {
    stdio: 'inherit',
  });

  // Start test service
  console.log('Starting test container...');
  execSync('docker compose -f docker-compose-test.yaml up uj1-pt-pt', {
    stdio: 'inherit',
  });
} catch (error) {
  console.error('Test setup failed:', error.message);
  process.exit(1);
}

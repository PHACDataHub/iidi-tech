import type {
  Bundle,
  Patient,
  AllergyIntolerance,
  Immunization,
  Resource,
} from 'fhir/r4.d.ts';

import { AppError } from './error_utils.ts';

function extractIdFromReference(reference: string): string {
  const parts = reference.split('/');
  return parts.length > 1 ? parts[1] : reference;
}

export function assert_bundle_follows_business_rules(
  _bundle: unknown,
): asserts _bundle is Bundle {
  if (!_bundle || typeof _bundle !== 'object') {
    throw new AppError(400, 'Invalid bundle: Bundle must be an object');
  }

  const bundle = _bundle as Bundle;

  if (bundle.resourceType !== 'Bundle') {
    throw new AppError(400, 'Invalid bundle: resourceType must be "Bundle"');
  }
  // Both write and validate operation end points allow entries to be empty
  if (
    !bundle.entry ||
    !Array.isArray(bundle.entry) ||
    bundle.entry.length === 0
  ) {
    throw new AppError(400, 'Invalid bundle: Bundle must contain entries');
  }

  const resources = bundle.entry
    .filter((entry) => entry.resource)
    .map((entry) => entry.resource as Resource);

  // Find all patients
  const patients = resources.filter(
    (resource) => resource.resourceType === 'Patient',
  ) as Patient[];

  // Must have exactly one Patient
  if (patients.length === 0) {
    throw new AppError(
      400,
      'Invalid bundle: Bundle must contain a Patient resource',
    );
  }
  if (patients.length > 1) {
    throw new AppError(
      400,
      'Invalid bundle: Bundle must contain exactly one Patient resource',
    );
  }

  const patientId = patients[0].id;
  if (!patientId) {
    throw new AppError(400, 'Invalid bundle: Patient resource must have an id');
  }

  // Get all allergies
  const allergies = resources.filter(
    (resource) => resource.resourceType === 'AllergyIntolerance',
  ) as AllergyIntolerance[];

  // All AllergyIntolerance resources must reference the single Patient.
  for (const allergy of allergies) {
    if (!allergy.patient || !allergy.patient.reference) {
      throw new AppError(
        400,
        `Invalid bundle: AllergyIntolerance ${allergy.id} must reference a patient`,
      );
    }

    const patientRef = allergy.patient.reference;
    const refPatientId = extractIdFromReference(patientRef);

    if (refPatientId !== patientId) {
      throw new AppError(
        400,
        `Invalid bundle: AllergyIntolerance ${allergy.id} references patient ${refPatientId}, but bundle patient is ${patientId}`,
      );
    }
  }

  // Get all immunizations
  const immunizations = resources.filter(
    (resource) => resource.resourceType === 'Immunization',
  ) as Immunization[];

  // All Immunization resources must reference the single Patient.
  for (const immunization of immunizations) {
    if (!immunization.patient || !immunization.patient.reference) {
      throw new AppError(
        400,
        `Invalid bundle: Immunization ${immunization.id} must reference a patient`,
      );
    }

    const patientRef = immunization.patient.reference;
    const refPatientId = extractIdFromReference(patientRef);

    if (refPatientId !== patientId) {
      throw new AppError(
        400,
        `Invalid bundle: Immunization ${immunization.id} references patient ${refPatientId}, but bundle patient is ${patientId}`,
      );
    }
  }

  // No unexpected resource types. Both validate and write operations perform this check. Adding this to define the scope of PoC.
  const allowedResourceTypes = [
    'Bundle',
    'Patient',
    'AllergyIntolerance',
    'Immunization',
  ];
  const unexpectedResources = resources.filter(
    (resource) => !allowedResourceTypes.includes(resource.resourceType),
  );

  if (unexpectedResources.length > 0) {
    const unexpectedTypes = unexpectedResources
      .map((resource) => resource.resourceType)
      .join(', ');

    throw new AppError(
      400,
      `Invalid bundle: Unexpected resource types found: ${unexpectedTypes}. Currently supported types are: ${allowedResourceTypes.join(', ')}`,
    );
  }
}

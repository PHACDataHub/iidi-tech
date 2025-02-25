import type { AllergyIntolerance, Immunization } from 'fhir/r4.d.ts';

import { AppError } from './error_utils.ts';
import {
  PATIENT_1,
  PATIENT_2,
  IMMUNIZATION_1,
  IMMUNIZATION_2,
  ALLERGY_INTOLERANCE_1,
  ALLERGY_INTOLERANCE_2,
  createTransactionBundle,
} from './test_utils.ts';
import { assert_bundle_follows_business_rules } from './validation_utils.ts';

describe('assert_bundle_follows_business_rules', () => {
  it('should not throw an error for a valid bundle with one patient', () => {
    const validBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_1,
      ALLERGY_INTOLERANCE_1,
    );

    expect(() => {
      assert_bundle_follows_business_rules(validBundle);
    }).not.toThrow();
  });

  it('should throw an error when bundle is not an object', () => {
    expect(() => {
      assert_bundle_follows_business_rules(null);
    }).toThrow(new AppError(400, 'Invalid bundle: Bundle must be an object'));

    expect(() => {
      assert_bundle_follows_business_rules('not an object');
    }).toThrow(new AppError(400, 'Invalid bundle: Bundle must be an object'));
  });

  it('should throw an error when resourceType is not "Bundle"', () => {
    const invalidBundle = {
      resourceType: 'NotBundle',
      entry: [{ resource: PATIENT_1 }],
    };

    expect(() => {
      assert_bundle_follows_business_rules(invalidBundle);
    }).toThrow(
      new AppError(400, 'Invalid bundle: resourceType must be "Bundle"'),
    );
  });

  it('should throw an error when bundle has no entries', () => {
    const emptyBundle = {
      resourceType: 'Bundle',
      entry: [],
    };

    expect(() => {
      assert_bundle_follows_business_rules(emptyBundle);
    }).toThrow(
      new AppError(400, 'Invalid bundle: Bundle must contain entries'),
    );

    const nullEntryBundle = {
      resourceType: 'Bundle',
      entry: null,
    };

    expect(() => {
      assert_bundle_follows_business_rules(nullEntryBundle);
    }).toThrow(
      new AppError(400, 'Invalid bundle: Bundle must contain entries'),
    );
  });

  it('should throw an error when bundle has no Patient resource', () => {
    // Create a bundle with only immunization and allergy, no patient
    const noPatientBundle = {
      resourceType: 'Bundle',
      entry: [
        { resource: IMMUNIZATION_1 },
        { resource: ALLERGY_INTOLERANCE_1 },
      ],
    };

    expect(() => {
      assert_bundle_follows_business_rules(noPatientBundle);
    }).toThrow(
      new AppError(
        400,
        'Invalid bundle: Bundle must contain a Patient resource',
      ),
    );
  });

  it('should throw an error when bundle has more than one Patient resource', () => {
    const multiplePatientBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_1,
      ALLERGY_INTOLERANCE_1,
    );

    // Add a second patient to the bundle
    multiplePatientBundle.entry.push({ resource: PATIENT_2 });

    expect(() => {
      assert_bundle_follows_business_rules(multiplePatientBundle);
    }).toThrow(
      new AppError(
        400,
        'Invalid bundle: Bundle must contain exactly one Patient resource',
      ),
    );
  });

  it('should throw an error when Patient has no id', () => {
    const patientWithoutId = { ...PATIENT_1, id: undefined };
    const invalidBundle = createTransactionBundle(
      patientWithoutId,
      IMMUNIZATION_1,
      ALLERGY_INTOLERANCE_1,
    );

    expect(() => {
      assert_bundle_follows_business_rules(invalidBundle);
    }).toThrow(
      new AppError(400, 'Invalid bundle: Patient resource must have an id'),
    );
  });

  it('should throw an error when AllergyIntolerance has no patient reference', () => {
    const allergyWithoutRef: unknown = {
      ...ALLERGY_INTOLERANCE_1,
      patient: undefined,
    };
    const invalidBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_1,
      allergyWithoutRef as AllergyIntolerance,
    );

    expect(() => {
      assert_bundle_follows_business_rules(invalidBundle);
    }).toThrow(
      new AppError(
        400,
        `Invalid bundle: AllergyIntolerance ${(allergyWithoutRef as AllergyIntolerance).id} must reference a patient`,
      ),
    );
  });

  it('should throw an error when AllergyIntolerance references wrong patient', () => {
    // ALLERGY_INTOLERANCE_2 references PATIENT_2, but we're including PATIENT_1
    const invalidBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_1,
      ALLERGY_INTOLERANCE_2,
    );

    expect(() => {
      assert_bundle_follows_business_rules(invalidBundle);
    }).toThrow(
      new AppError(
        400,
        `Invalid bundle: AllergyIntolerance ${ALLERGY_INTOLERANCE_2.id} references patient ${PATIENT_2.id}, but bundle patient is ${PATIENT_1.id}`,
      ),
    );
  });

  it('should throw an error when Immunization has no patient reference', () => {
    const immunizationWithoutRef: unknown = {
      ...IMMUNIZATION_1,
      patient: undefined,
    };
    const invalidBundle = createTransactionBundle(
      PATIENT_1,
      immunizationWithoutRef as Immunization,
      ALLERGY_INTOLERANCE_1,
    );

    expect(() => {
      assert_bundle_follows_business_rules(invalidBundle);
    }).toThrow(
      new AppError(
        400,
        `Invalid bundle: Immunization ${(immunizationWithoutRef as Immunization).id} must reference a patient`,
      ),
    );
  });

  it('should throw an error when Immunization references wrong patient', () => {
    // IMMUNIZATION_2 references PATIENT_2, but we're including PATIENT_1
    const invalidBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_2,
      ALLERGY_INTOLERANCE_1,
    );

    expect(() => {
      assert_bundle_follows_business_rules(invalidBundle);
    }).toThrow(
      new AppError(
        400,
        `Invalid bundle: Immunization ${IMMUNIZATION_2.id} references patient ${PATIENT_2.id}, but bundle patient is ${PATIENT_1.id}`,
      ),
    );
  });

  it('should throw an error when bundle contains unsupported resource types', () => {
    const validBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_1,
      ALLERGY_INTOLERANCE_1,
    );

    // In the currently defined scope, Observation is not allowed
    validBundle.entry.push({
      resource: {
        resourceType: 'Observation',
        code: { text: 'Test Observation' },
        status: 'final',
      },
    });

    const allowedTypes = [
      'Bundle',
      'Patient',
      'AllergyIntolerance',
      'Immunization',
    ];

    expect(() => {
      assert_bundle_follows_business_rules(validBundle);
    }).toThrow(
      new AppError(
        400,
        `Invalid bundle: Unexpected resource types found: Observation. Currently supported types are: ${allowedTypes.join(', ')}`,
      ),
    );
  });

  it('should validate a complex bundle with multiple resources of allowed types', () => {
    const validBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_1,
      ALLERGY_INTOLERANCE_1,
    );

    // Add another immunization and allergy for the same patient
    const immunization2 = {
      ...IMMUNIZATION_1,
      id: 'imm-extra',
    };
    const allergy2 = {
      ...ALLERGY_INTOLERANCE_1,
      id: 'allergy-extra',
    };

    validBundle.entry.push({ resource: immunization2 });
    validBundle.entry.push({ resource: allergy2 });

    expect(() => {
      assert_bundle_follows_business_rules(validBundle);
    }).not.toThrow();
  });
});

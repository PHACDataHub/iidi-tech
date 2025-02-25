import type {
  AllergyIntolerance,
  BundleEntry,
  Immunization,
  Patient,
} from 'fhir/r4.d.ts';

// Patient 1 Data
const PATIENT_1: Patient = {
  resourceType: 'Patient',
  id: 'patient-1',
  name: [
    {
      family: 'Doe',
      given: ['John', 'Michael'],
    },
  ],
  gender: 'male',
  birthDate: '1990-06-15',
  address: [
    {
      line: ['1234 Main St'],
      city: 'Vancouver',
      state: 'BC',
      postalCode: 'V6B 3L1',
      country: 'CA',
    },
  ],
  identifier: [
    {
      system: 'https://healthcare.example.org/ids',
      value: 'abcdef123456',
    },
    {
      system: 'https://healthcare.example.org/healthcard',
      value: '1234567890',
    },
  ],
};

// Patient 2 Data
const PATIENT_2: Patient = {
  resourceType: 'Patient',
  id: 'patient-2',
  name: [
    {
      family: 'Smith',
      given: ['Jane', 'Alice'],
    },
  ],
  gender: 'female',
  birthDate: '1985-02-25',
  address: [
    {
      line: ['5678 Oak St'],
      city: 'Toronto',
      state: 'ON',
      postalCode: 'M5A 1T1',
      country: 'CA',
    },
  ],
  identifier: [
    {
      system: 'https://healthcare.example.org/ids',
      value: 'ghijk789012',
    },
    {
      system: 'https://healthcare.example.org/healthcard',
      value: '9876543210',
    },
  ],
};

// Immunization Data for Patient 1

const IMMUNIZATION_1: Immunization = {
  resourceType: 'Immunization',
  patient: {
    reference: 'Patient/patient-1',
  },
  vaccineCode: {
    coding: [
      {
        system: 'https://hl7.org/fhir/sid/cvx',
        code: '03',
        display: 'MMR',
      },
    ],
  },
  occurrenceDateTime: '2023-05-20',
  manufacturer: {
    display: 'Pfizer',
  },
  lotNumber: 'MMR12345',
  site: {
    coding: [
      {
        display: 'Left Arm',
      },
    ],
  },
  status: 'completed',
  reaction: [
    {
      date: '2023-05-21',
    },
    {
      date: '2023-05-22',
    },
  ],
};

// Immunization Data for Patient 2
const IMMUNIZATION_2: Immunization = {
  resourceType: 'Immunization',
  patient: {
    reference: 'Patient/patient-2',
  },
  vaccineCode: {
    coding: [
      {
        system: 'https://hl7.org/fhir/sid/cvx',
        code: '03',
        display: 'MMR',
      },
    ],
  },
  occurrenceDateTime: '2024-01-15',
  manufacturer: {
    display: 'Moderna',
  },
  lotNumber: 'MMR67890',
  site: {
    coding: [
      {
        display: 'Right Arm',
      },
    ],
  },
  status: 'completed',
  reaction: [
    {
      date: '2024-01-16',
    },
    {
      date: '2024-01-17',
    },
  ],
};

// AllergyIntolerance for patient 1
const ALLERGY_INTOLERANCE_1: AllergyIntolerance = {
  resourceType: 'AllergyIntolerance',
  patient: {
    reference: 'Patient/patient-1',
  },
  clinicalStatus: {
    coding: [
      {
        code: 'rest',
      },
    ],
  },
  code: {
    coding: [
      {
        system: 'https://snomed.info/sct',
        code: '91935009',
        display: 'Allergy to egg protein',
      },
    ],
  },
  criticality: 'high',
  type: 'allergy',
  note: [
    {
      text: 'Patient has a severe reaction to egg protein, which may cause anaphylaxis.',
    },
  ],
  onsetDateTime: '2023-05-20',
};

// AllergyIntolerance for Patient 2
const ALLERGY_INTOLERANCE_2: AllergyIntolerance = {
  resourceType: 'AllergyIntolerance',
  patient: {
    reference: 'Patient/patient-2',
  },
  code: {
    coding: [
      {
        system: 'https://snomed.info/sct',
        code: '91934004',
        display: 'Allergy to gelatin',
      },
    ],
  },
  criticality: 'low',
  type: 'allergy',
  note: [
    {
      text: 'Patient experiences mild skin reactions when exposed to gelatin.',
    },
  ],
  onsetDateTime: '2023-07-15',
};

function createTransactionBundle(
  patient: Patient | null,
  immunization: Immunization | null,
  adverseEvent: AllergyIntolerance | null,
) {
  const entries: BundleEntry[] = [];

  if (patient) {
    entries.push({
      resource: patient,
      request: {
        method: 'POST',
        url: 'Patient',
      },
    });
  }

  if (immunization) {
    entries.push({
      resource: immunization,
      request: {
        method: 'POST',
        url: 'Immunization',
      },
    });
  }

  if (adverseEvent) {
    entries.push({
      resource: adverseEvent,
      request: {
        method: 'POST',
        url: 'AllergyIntolerance',
      },
    });
  }

  return {
    resourceType: 'Bundle',
    type: 'transaction',
    entry: entries,
  };
}

export {
  PATIENT_1,
  PATIENT_2,
  IMMUNIZATION_1,
  IMMUNIZATION_2,
  ALLERGY_INTOLERANCE_1,
  ALLERGY_INTOLERANCE_2,
  createTransactionBundle,
};
